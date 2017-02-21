#!/usr/bin/python3
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
from systemd import journal


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

j = journal.Reader(journal.SYSTEM)
j.this_boot()
j.log_level(journal.LOG_DEBUG)

print("\nWake/Suspend Time SystemD Journal Analyzer [current boot]\n")

# take timestamp of first entry in list as boot time
bootTime = j.get_next()['__REALTIME_TIMESTAMP']

# Kernel messages lingo: Hibernation = to disk; Suspend = to RAM; 
# Sleep = either hibernation (S4) or suspend (S3)
suspendStart = "Reached target Sleep."
hibernateStart = "Suspending system..."
suspendWake = "ACPI: Waking up from system sleep state S3"
hibernateWake = "ACPI: Waking up from system sleep state S4"
# Starting Sleep (applies to both Suspend and Hibernation): Suspending system...

j.add_match("MESSAGE=" + hibernateStart)
j.add_disjunction()
j.add_match("MESSAGE=" + suspendStart)
j.add_disjunction()
j.add_match("MESSAGE=" + hibernateWake)
j.add_disjunction()
j.add_match("MESSAGE=" + suspendWake)

print("Initial Boot Timestamp: ", bootTime.strftime("%Y-%m-%d %H:%M:%S"), "\n")

# times is an array of [(start-boot, suspend), (wakeup, suspend), ...]

times = []  # list of (wakeup, suspend) timestamps, starting with the cold boot

lookingForSleep = True
wakeUpCandidate = bootTime
wakeUpCandidateType = "Cold Boot"
sleepCandidate = None
# When the lookingForSleep flag is On, keep looking for a suspend event until a Wakeup is found
# this will allow the script to handle sequences of "N" repeated suspends in the log
#    Result: assumes the last Suspend found in the sequence as the right one (validated)
# simlar logic used to handle "N" repeated wakeUps in the log
#    Result: assumes the first Wakeup found in the sequence as the right one (validated)
# Repeated Suspends can happen in the log if the suspend is aborted via suspend-hook scripts

for entry in j:
    try:
        str(entry['MESSAGE'])        
    except:
        continue
    #print(str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE'])
    if lookingForSleep:
        if suspendStart in str(entry['MESSAGE']) or hibernateStart in str(entry['MESSAGE']):
            sleepCandidate = entry['__REALTIME_TIMESTAMP']
        if (suspendWake in str(entry['MESSAGE']) or hibernateWake in str(entry['MESSAGE'])) \
            and sleepCandidate != None:
            # found a wakeup while looking for sleep (S3 or S4)
            # so: accept the previous sleep as a Good one and add the entry
            times.append((wakeUpCandidate, sleepCandidate, wakeUpCandidateType))
            # capture the wakeUpCandidate and switch to looking for WakeUps                      
            wakeUpCandidate = entry['__REALTIME_TIMESTAMP']
            if suspendWake in str(entry['MESSAGE']): wakeUpCandidateType = "S3 (RAM)" 
            elif hibernateWake in str(entry['MESSAGE']): wakeUpCandidateType = "S4 (disk)" 
            lookingForSleep = False
    else:
        #looking for WakeUps
        if suspendWake in str(entry['MESSAGE']) or hibernateWake in str(entry['MESSAGE']):
            # ignore the entry: we want to keep the first WakeUp in the sequence
            pass
        if suspendStart in str(entry['MESSAGE']) or hibernateStart in str(entry['MESSAGE']):
            sleepCandidate = entry['__REALTIME_TIMESTAMP']            
            lookingForSleep = True
             
# appending the last wakeUp with the current time
times.append((wakeUpCandidate, datetime.datetime.now(), wakeUpCandidateType))

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

# if there is at least one item (should always be)
if len(times) > 0:
    for i in times:
        awakeTime = calculateTimeDiference(i[1], i[0])
        row = [
            i[0].strftime("%Y-%m-%d %H:%M:%S"),
            i[1].strftime("%Y-%m-%d %H:%M:%S"),
            timeDiff_format.format(awakeTime[0], awakeTime[1]),
            i[2]
        ]
        matrix.append(row)
        totalDaysAwake = totalDaysAwake + awakeTime[3]

# removing the latest time, because it is still this boot
matrix[-1][-3] = '(Still Awake)'

for row in matrix:
    print(row_format.format(*row))

print(row_format.format(*rowSeparator), "\n")


timeSinceBoot = calculateTimeDiference(datetime.datetime.now(), bootTime)
# provide a summary
print(
    str(
        "Days Since Boot: " +
        "{:.2f}".format(timeSinceBoot[3]) +
        " - Days Awake: " +
        "{:.2f}".format(totalDaysAwake) +
        " - Sleep/Wake Cycles: " +
        str(len(times) - 1) +
        "\n"
    )
)
