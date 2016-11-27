#!/usr/bin/python3
"""
Parses the systemd journal to find out:
time of last cold boot, and start/end times of each suspend/resume cycle
and their duration
(c) 2016 Ariel

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

# echo
# echo ">> [SUSPEND] Times during current boot"
# journalctl -b 0 |grep "]: Suspending system..."
# echo
# echo ">> [WAKE] Times during current boot"
# journalctl -b 0 |grep "PM: Finishing wakeup"
# echo

import datetime
from systemd import journal
import threading
import time


class cursorSpinner(threading.Thread):
    """Diplays a static message followed by
    a spinning cursor in the terminal"""

    def __init__(self, messageString, refreshInterval):
        self.flag = True
        self.animation_char = "|/-\\"
        self.messageString = messageString
        self.refreshInterval = refreshInterval
        self.idx = 0
        threading.Thread.__init__(self)

    def run(self):
        while self.flag:
            print('\r' + self.messageString, end='')
            print(
                self.animation_char[self.idx % len(self.animation_char)],
                end=''
            )
            self.idx += 1
            time.sleep(self.refreshInterval)

    def stop(self):
        self.flag = False


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
# j.add_match(_SYSTEMD_UNIT="systemd-udevd.service")

print("\nWake/Suspend Time SystemD Journal Analyzer [current boot]\n")

# take timestamp of first entry in list as boot time
bootTime = j.get_next()['__REALTIME_TIMESTAMP']
print("Initial Boot Timestamp: ", bootTime.strftime("%Y-%m-%d %H:%M:%S"), "\n")

j.add_match("MESSAGE=Suspending system...")
j.add_disjunction()
j.add_match("MESSAGE=PM: Finishing wakeup.")

spinningCursor = cursorSpinner("[Analyzing Journal] ...", 0.2)
spinningCursor.start()

# times is an array of [(start-boot, suspend), (wakeup, suspend), ...]
times = []
tmp = bootTime

for entry in j:
    try:
        str(entry['MESSAGE'])
    except:
        continue
    # print(str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE'])
    if "Suspending system..." in str(entry['MESSAGE']):
        times.append((tmp, entry['__REALTIME_TIMESTAMP']))
        tmp = None
    if "Finishing wakeup" in str(entry['MESSAGE']):
        tmp = entry['__REALTIME_TIMESTAMP']

# appending the last wakeup with the current time
if tmp is not None:
    times.append((tmp, datetime.datetime.now()))

spinningCursor.stop()
print(" ", end='\r')

# prints three columns
# Wake Time   |   Suspend Time    |    Awake Time
# first row contains boot time
# last row contains last awake time but no 'suspend time'

headers = ["Wake Timestamp", "Suspend Timestamp", "Awake Time"]
row_format = "  {:^21} |" * (len(headers))
timeDiff_format = "{:3d}h {:2d}m"
print(row_format.format(*headers))
print(row_format.format("-" * 20, "-" * 20, "-" * 20))

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
            timeDiff_format.format(awakeTime[0], awakeTime[1])
        ]
        matrix.append(row)
        totalDaysAwake = totalDaysAwake + awakeTime[3]

# removing the latest time, because it is still this boot
matrix[-1][-2] = '(Still Awake)'

for row in matrix:
    print(row_format.format(*row))

print(row_format.format("-" * 20, "-" * 20, "-" * 20), "\n")


timeSinceBoot = calculateTimeDiference(datetime.datetime.now(), bootTime)
# provide a summary
print(
    str(
        "Summary: Days Since Boot [" +
        "{:.2f}".format(timeSinceBoot[3]) +
        "] | Days Awake [" +
        "{:.2f}".format(totalDaysAwake) +
        "] | Suspend/Wake Cycles: [" +
        str(len(times) - 1) +
        "]\n"
    )
)
