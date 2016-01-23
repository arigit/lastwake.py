#!/usr/bin/python3
"""
Parses the systemd journal to find out: time of last cold boot, and start/end times of each suspend/resume cycle
and their duration
(c) Ariel - 2016
"""

# echo 
# echo ">> [SUSPEND] Times during current boot"
# journalctl -b 0 |grep "]: Suspending system..."
# echo 
# echo ">> [WAKE] Times during current boot"
# journalctl -b 0 |grep "PM: Finishing wakeup"
# echo

import datetime
import select
from systemd import journal
import sys
import threading
import time


class cursorSpinner(threading.Thread):
    """ Diplays a static message followed by a spinning cursor in the terminal
    """
    def __init__(self, messageString, refreshInterval):
        self.flag = True
        self.animation_char = "|/-\\"
        self.messageString = messageString
        self.refreshInterval = refreshInterval
        self.idx = 0
        threading.Thread.__init__(self)

    def run(self):
        while self.flag:
            print('\r'+self.messageString, end='')
            print(self.animation_char[self.idx % len(self.animation_char)], end='')
            self.idx += 1
            time.sleep(self.refreshInterval)

    def stop(self):
        self.flag = False
        
        
def calculateTimeDiference(suspendTime, awakeTime):
    # returns a 'datetime.time' object with the time diference in hours/minutes/seconds
    # Instead of a timedelta object, it returns a list of 3 integers [hours, minutes, seconds]
    awakeSeconds = (suspendTime-awakeTime).total_seconds()
    awakeFractionalDays = awakeSeconds / 86400
    awakeHours = int(awakeSeconds // 3600)
    awakeMinutes = int((awakeSeconds % 3600) // 60)
    awakeSeconds = int(awakeSeconds % 60)
    awakeTime = [awakeHours, awakeMinutes, awakeSeconds, awakeFractionalDays]
    return awakeTime
    

# Main Program 

j = journal.Reader()
j.this_boot()
j.log_level(journal.LOG_DEBUG)
# j.add_match(_SYSTEMD_UNIT="systemd-udevd.service")

print("\nWake/Suspend Time SystemD Journal Analyzer [current boot]\n")

# take timestamp of first entry in list as boot time
bootTime = j.get_next()['__REALTIME_TIMESTAMP']
print("Initial Boot Timestamp: ", bootTime.strftime("%Y-%m-%d %H:%M:%S"), "\n")


spinningCursor = cursorSpinner("[Analyzing Journal] ...", 0.2)
spinningCursor.start()

suspendTimes = []
wakeTimes = []

for entry in j:    
    #print(str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE'])
    if "Suspending system..." in entry['MESSAGE']:
        suspendTimes.append(entry['__REALTIME_TIMESTAMP'])
    if "Finishing wakeup" in entry['MESSAGE']:
        wakeTimes.append(entry['__REALTIME_TIMESTAMP'])
    

#time.sleep(3)
spinningCursor.stop()
print(" ", end='\r')


#print("Suspend Timestamps:", suspendTimes)
#print("Wake Timestamps:", wakeTimes)

# prints three columns
# Wake Time   |   Suspend Time    |    Awake Time
# first row contains boot time
# last row contains last awake time but no 'suspend time'

headers = ["Wake Timestamp", "Suspend Timestamp", "Awake Time"]
row_format = "  {:^21} |" * (len(headers))
timeDiff_format = "{:3d}h {:2d}m"
print(row_format.format(*headers))
print (row_format.format("-"*20, "-"*20, "-"*20))

# assemble matrix rows
matrix = []
totalDaysAwake = 0

# first row
awakeTime = calculateTimeDiference(suspendTimes[0], bootTime)
row = [bootTime.strftime("%Y-%m-%d %H:%M:%S"), suspendTimes[0].strftime("%Y-%m-%d %H:%M:%S"), timeDiff_format.format(awakeTime[0],awakeTime[1]) ]
matrix.append(row)
totalDaysAwake = totalDaysAwake + awakeTime[3]

# create rest of matrix
rowCounter = 1
for rowCounter in range(1,len(wakeTimes)):
    awakeTime = calculateTimeDiference(suspendTimes[rowCounter], wakeTimes[rowCounter-1])
    row = [wakeTimes[rowCounter-1].strftime("%Y-%m-%d %H:%M:%S"), suspendTimes[rowCounter].strftime("%Y-%m-%d %H:%M:%S"), timeDiff_format.format(awakeTime[0],awakeTime[1])]
    matrix.append(row)
    totalDaysAwake = totalDaysAwake + awakeTime[3]

# final row
awakeTime = calculateTimeDiference(datetime.datetime.now(), wakeTimes[rowCounter])
row = [wakeTimes[rowCounter].strftime("%Y-%m-%d %H:%M:%S"), "(Still Awake)", timeDiff_format.format(awakeTime[0],awakeTime[1])]
matrix.append(row)
totalDaysAwake = totalDaysAwake + awakeTime[3]

for row in matrix:
    print(row_format.format(*row))

print (row_format.format("-"*20, "-"*20, "-"*20), "\n")


timeSinceBoot = calculateTimeDiference(datetime.datetime.now(), bootTime)
# provide a summary
print("Summary: Days Since Boot [" + "{:.2f}".format(timeSinceBoot[3]) + "] | Days Awake [" + "{:.2f}".format(totalDaysAwake) + "] | Suspend/Wake Cycles: [" + str(len(wakeTimes)) + "]\n")
