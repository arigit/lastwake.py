#!/usr/bin/env python3
"""
Parses the systemd journal to find out:
time of last cold boot, and start/end times of each sleep/resume cycle
and their duration - supports S3 (suspend to RAM) and S4 (hibernate to disk)
(c) 2017 Ariel

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import datetime
import sys
from systemd import journal
import argparse
import subprocess



def calculateTimeDiference(suspendTime, awakeTime):
    """returns a 'datetime.time' object
    with the time diference in hours/minutes/seconds
    Instead of a timedelta object, it returns
    a list of 3 integers [hours, minutes, seconds]
    """
    awakeSeconds = (suspendTime - awakeTime).total_seconds()
    awakeFractionalDays = awakeSeconds / 86400
    awakeHours = int(awakeSeconds // 3600)
    awakeMinutes = int((awakeSeconds % 3600) // 60)
    awakeSeconds = int(awakeSeconds % 60)
    awakeTime = [awakeHours, awakeMinutes, awakeSeconds, awakeFractionalDays]
    return awakeTime


# Main Program
if __name__ == '__main__':


    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--boot-id', help="boot-id in the format obtained from 'journalctl --list-boots'", action="store")
    parser.add_argument('bootId', help="optional: boot-id in the format obtained from 'journalctl --list-boots'", nargs='?')

    args = parser.parse_args()                  
    
    
    if not len(sys.argv) > 1: 
        # if no arguments, assume current boot
        bootId = None
        msg = 'current boot'
    elif args.boot_id:
        bootId = args.boot_id
        msg = 'selected boot = ' + bootId
    else:
        bootId = args.bootId
        msg = 'selected boot = ' + bootId

    if bootId and bootId.startswith("-"):
        bId = int(bootId)
        assert bId <= 0
        out = subprocess.check_output(["journalctl",
                                       "--list-boots"]).decode('utf-8')
        boots = {
            int(l[0]): l[1]
            for l in map(lambda x: x.strip().split(" "),
                         out.strip().split("\n")) if l
        }
        if bId in boots:
            bootId = boots[bId]
        
      

    j = journal.Reader(journal.SYSTEM)
    j.this_boot(bootId)
    j.add_conjunction()
    j.log_level(journal.LOG_DEBUG)

    print("\nWake/Sleep Time SystemD Journal Analyzer\n")
    print(" Boot under analysis: " + msg)

    try:
        # take timestamp of first entry in list as boot time
        bootTime = j.get_next()['__REALTIME_TIMESTAMP']
    except KeyError:
        print("\n Warning: no entries in the Journal found for boot: " + bootId + " (script terminated)\n")
        sys.exit(1)

    # Kernel messages lingo: Hibernation = to disk; Suspend = to RAM;
    # Sleep = either hibernation (S4) or suspend (S3)
    suspendStart = "Reached target Sleep."
    hibernateStart = "Suspending system..."
    suspendWake = "ACPI: Waking up from system sleep state S3"
    hibernateWake = "ACPI: Waking up from system sleep state S4"
    shuttingDown = "Shutting down."
    # Starting Sleep (applies to both Suspend and Hibernation): Suspending system...

    j.add_match("MESSAGE=" + hibernateStart)
    j.add_disjunction()
    j.add_match("MESSAGE=" + suspendStart)
    j.add_disjunction()
    j.add_match("MESSAGE=" + hibernateWake)
    j.add_disjunction()
    j.add_match("MESSAGE=" + suspendWake)
    j.add_disjunction()
    j.add_match("MESSAGE=" + shuttingDown)

    print(" Initial Boot Timestamp: ", bootTime.strftime("%Y-%m-%d %H:%M:%S"), "\n")

    # times is an array of [(start-boot, suspend), (wakeup, suspend), ...]

    times = []  # list of (wakeup, suspend) timestamps, starting with the cold boot

    wakeUpCandidate = bootTime
    wakeUpCandidateType = "S5 (boot)"
    sleepCandidate = None
    # Keep the latest suspend event until a Wakeup is found
    # this will allow the script to handle sequences of "N" repeated suspends in the log
    #    Result: assumes the last Suspend found in the sequence as the right one
    # simlar logic used to handle "N" repeated wakeUps in the log
    #    Result: assumes the first Wakeup found in the sequence as the right one (otherwise sleepCandidate is None)
    # Repeated Suspends can happen in the log if the suspend is aborted via suspend-hook scripts

    for entry in j:
        try:
            msg = str(entry['MESSAGE'])
        except:
            continue
        #print(str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE'])
        if suspendStart in msg or hibernateStart in msg or shuttingDown in msg:
            sleepCandidate = entry['__REALTIME_TIMESTAMP']
        elif (suspendWake in msg or hibernateWake in msg) \
            and sleepCandidate is not None:
            # found a wakeup: add the previous Wake along with the latest sleep
            times.append((wakeUpCandidate, sleepCandidate, wakeUpCandidateType))
            # capture the wakeUpCandidate and switch to looking for WakeUps
            wakeUpCandidate = entry['__REALTIME_TIMESTAMP']
            sleepCandidate = None
            if suspendWake in msg: wakeUpCandidateType = "S3 (RAM)"
            elif hibernateWake in msg: wakeUpCandidateType = "S4 (disk)"

    # append the last wakeUp with the sleepCandidate (might be None if still awake)
    times.append((wakeUpCandidate, sleepCandidate, wakeUpCandidateType))

    j.close()
    print(" ", end='\r')

    # prints three columns
    # Wake Time   |   Suspend Time    |    Awake Time
    # first row contains boot time
    # last row contains last awake time but no 'suspend time'

    headers = ["Wake Timestamp", "Sleep Timestamp", "Awake Time", "Wake From"]
    row_format = " {:^19} |" * 2 + " {:^10} |" + " {:^9}"
    timeDiff_format = "{:3d}h {:2d}m"
    print(row_format.format(*headers))
    rowSeparator = ("-" * 19, "-" * 19, "-" * 10, "-" * 9)
    print(row_format.format(*rowSeparator))

    # assemble matrix rows
    matrix = []
    totalDaysAwake = 0

    defaultFormat = "%Y-%m-%d %H:%M:%S"
    # Create a string array with the infos
    for i in times:
        [start, end, bootType] = i
        if end is None:
            end = datetime.datetime.now()
            endFormat = '(Still Awake)'
        else:
            endFormat = defaultFormat
        lastTime = end
        awakeTime = calculateTimeDiference(end, start)
        row = [
            start.strftime(defaultFormat),
            end.strftime(endFormat),
            timeDiff_format.format(awakeTime[0], awakeTime[1]),
            bootType
        ]
        matrix.append(row)
        totalDaysAwake = totalDaysAwake + awakeTime[3]

    for row in matrix:
        print(row_format.format(*row))

    print(row_format.format(*rowSeparator), "\n")


    timeSinceBoot = calculateTimeDiference(lastTime, bootTime)
    # print(lastTime)
    # provide a summary
    print(
        str(
            "Days Since Boot: " +
            "{:.2f}".format(timeSinceBoot[3]) +
            " - Days Awake: " +
            "{:.2f}".format(totalDaysAwake) +
            " - Wake/Sleep Cycles: " +
            str(len(times) - 1) +
            "\n"
        )
    )
