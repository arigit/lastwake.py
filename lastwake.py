#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2017-2026 Ariel
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Parses the systemd journal to find out:
time of last cold boot, and start/end times of each sleep/resume cycle
and their duration - supports S3 (suspend to RAM), s2idle and
S4 (hibernate to disk)
"""

import argparse
import datetime
import json
import subprocess
import sys

from systemd import journal


def calculateTimeDifference(endTime, startTime):
    """Returns the elapsed time between startTime and endTime as a list of
    4 values: [hours, minutes, seconds, fractionalDays]
    """
    totalSeconds = (endTime - startTime).total_seconds()
    return [
        int(totalSeconds // 3600),
        int((totalSeconds % 3600) // 60),
        int(totalSeconds % 60),
        totalSeconds / 86400,
    ]


def runJournalctl(extraArgs):
    """Runs journalctl and returns its stdout, or None if it is unavailable
    or exits with an error."""
    try:
        result = subprocess.run(["journalctl"] + extraArgs,
                                capture_output=True, encoding="utf8")
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def parseBootTable(out):
    """Parses the human readable output of 'journalctl --list-boots'.

    Handles both layouts: the original 'index boot-id first last' lines and
    the systemd >= 254 table, which adds an IDX/BOOT ID header row and pads
    the columns. Any line whose first field is not an integer is skipped,
    which discards the header without needing to know the systemd version.
    """
    boots = {}
    for line in out.splitlines():
        fields = line.split()
        if len(fields) < 2:
            continue
        try:
            index = int(fields[0])
        except ValueError:
            continue
        boots[index] = fields[1]
    return boots


def resolveBootOffset(offset, parser):
    """Maps a relative boot index (0, -1, -2, ...) to its boot id.

    Prefers the JSON output of 'journalctl --list-boots' (systemd >= 250)
    and falls back to parsing the text table on older releases, where -o json
    is either rejected or silently ignored for --list-boots.
    """
    out = runJournalctl(["--list-boots", "-o", "json"])
    if not out:
        out = runJournalctl(["--list-boots"])
    if not out:
        parser.error("could not read the boot list from journalctl")

    try:
        boots = {int(b["index"]): str(b["boot_id"]) for b in json.loads(out)}
    except (ValueError, TypeError, KeyError):
        # not JSON: older systemd printed the table regardless of -o json
        boots = parseBootTable(out)

    if not boots:
        parser.error("journalctl reported no boots")
    if offset not in boots:
        parser.error("boot %d is not in the journal (available: %d to 0)"
                     % (offset, min(boots)))
    return boots[offset]


# Main Program
if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Wake/Sleep time systemd journal analyzer")
    parser.add_argument('-b', '--boot-id', action="store",
                        help="boot-id in the format obtained from "
                             "'journalctl --list-boots', or a relative "
                             "offset such as -1")
    parser.add_argument('bootId', nargs='?',
                        help="optional: same as --boot-id, given positionally")
    parser.add_argument('-s', '--seconds-since-last-wake-up',
                        action="store_true",
                        help="prints the number of seconds elapsed since the "
                             "last wake-up event")

    args = parser.parse_args()

    bootId = args.boot_id or args.bootId

    if bootId and bootId.startswith("-"):
        try:
            bootOffset = int(bootId)
        except ValueError:
            parser.error("'%s' is not a valid boot id or boot offset" % bootId)
        if bootOffset > 0:
            parser.error("boot offsets must be 0 or negative")
        bootId = resolveBootOffset(bootOffset, parser)

    bootUnderAnalysis = ('selected boot = ' + bootId) if bootId \
        else 'current boot'

    j = journal.Reader(journal.SYSTEM)
    j.this_boot(bootId)
    j.add_conjunction()
    j.log_level(journal.LOG_DEBUG)

    try:
        # take timestamp of first entry in list as boot time
        bootTime = j.get_next()['__REALTIME_TIMESTAMP']
    except KeyError:
        print("\n Warning: no entries in the Journal found for "
              + bootUnderAnalysis + " (script terminated)\n")
        sys.exit(1)

    # Kernel messages lingo: Hibernation = to disk; Suspend = to RAM;
    # Sleep = either hibernation (S4) or suspend (S3/s2idle)
    # These strings are matched exactly by add_match(), so each variant a
    # kernel/systemd version might emit needs its own entry.
    suspendStartList = ["Entering sleep state 'suspend'...",
                        "Reached target Sleep.",
                        "PM: suspend entry (deep)",
                        "PM: suspend entry (s2idle)"]
    hibernateStartList = ["Suspending system...",
                          "PM: hibernation: hibernation entry"]
    shuttingDownList = ["Shutting down."]
    suspendWakeList = ["ACPI: PM: Waking up from system sleep state S3",
                       "ACPI: Waking up from system sleep state S3"]
    hibernateWakeList = ["ACPI: PM: Waking up from system sleep state S4",
                         "ACPI: Waking up from system sleep state S4",
                         "PM: hibernation: hibernation exit"]
    # s2idle systems (most modern laptops/NUCs) never log an ACPI S3 wake;
    # 'PM: suspend exit' is the fallback. On deep-suspend systems it is also
    # logged, but the ACPI line arrives first and wins, so the S3 label holds.
    s2idleWakeList = ["PM: suspend exit"]

    sleepMatches = suspendStartList + hibernateStartList + shuttingDownList
    wakeMatches = suspendWakeList + hibernateWakeList + s2idleWakeList

    for item in (sleepMatches + wakeMatches):
        j.add_match("MESSAGE=" + item)
        j.add_disjunction()

    # the boot timestamp was read before the message filters existed, so
    # rewind to make sure the loop below starts from the first match
    j.seek_head()

    # times is an array of [(start-boot, suspend), (wakeup, suspend), ...]

    times = []  # list of (wakeup, suspend) timestamps, starting with the cold boot

    wakeUpCandidate = bootTime
    wakeUpCandidateType = "S5 (boot)"
    sleepCandidate = None
    shutdownTime = None
    # Keep the latest suspend event until a Wakeup is found
    # this will allow the script to handle sequences of "N" repeated suspends in the log
    #    Result: assumes the last Suspend found in the sequence as the right one
    # simlar logic used to handle "N" repeated wakeUps in the log
    #    Result: assumes the first Wakeup found in the sequence as the right one (otherwise sleepCandidate is None)
    # Repeated Suspends can happen in the log if the suspend is aborted via suspend-hook scripts

    for entry in j:
        try:
            msg = str(entry['MESSAGE'])
            timestamp = entry['__REALTIME_TIMESTAMP']
        except KeyError:
            continue

        if any(i in msg for i in shuttingDownList):
            # a shutdown closes the last awake period; it is not a sleep
            sleepCandidate = timestamp
            shutdownTime = timestamp
        elif any(i in msg for i in (suspendStartList + hibernateStartList)):
            sleepCandidate = timestamp
        elif (sleepCandidate is not None
                and any(i in msg for i in wakeMatches)):
            # found a wakeup: add the previous Wake along with the latest sleep
            times.append((wakeUpCandidate, sleepCandidate, wakeUpCandidateType))
            # capture the wakeUpCandidate and switch to looking for WakeUps
            wakeUpCandidate = timestamp
            sleepCandidate = None
            shutdownTime = None
            if any(x in msg for x in suspendWakeList):
                wakeUpCandidateType = "S3 (RAM)"
            elif any(x in msg for x in hibernateWakeList):
                wakeUpCandidateType = "S4 (disk)"
            else:
                wakeUpCandidateType = "s2idle"

    # append the last wakeUp with the sleepCandidate (might be None if still awake)
    times.append((wakeUpCandidate, sleepCandidate, wakeUpCandidateType))

    j.close()

    # prepares the column content for printing
    # Wake Time   |   Suspend Time    |    Awake Time
    # first row contains boot time
    # last row contains last awake time but no 'suspend time'

    headers = ["Wake Timestamp", "Sleep Timestamp", "Awake Time", "Wake From"]
    row_format = " {:^19} |" * 2 + " {:^10} |" + " {:^9}"
    timeDiff_format = "{:3d}h {:2d}m"
    rowSeparator = ("-" * 19, "-" * 19, "-" * 10, "-" * 9)

    # assemble matrix rows
    matrix = []
    totalDaysAwake = 0
    secondsSinceLastWakeUp = 0
    lastTime = bootTime

    defaultFormat = "%Y-%m-%d %H:%M:%S"
    # Create a string array with the infos
    for i in times:
        [start, end, bootType] = i
        if end is None:
            if start.tzinfo is not None and start.tzinfo.utcoffset(start) is not None:
                end = datetime.datetime.now(tz=datetime.timezone.utc)
            else:
                end = datetime.datetime.now()
            endFormat = '(Still Awake)'
            secondsSinceLastWakeUp = (end - start).total_seconds()
        else:
            endFormat = defaultFormat
        lastTime = end
        awakeTime = calculateTimeDifference(end, start)
        row = [
            start.strftime(defaultFormat),
            end.strftime(endFormat),
            timeDiff_format.format(awakeTime[0], awakeTime[1]),
            bootType
        ]
        matrix.append(row)
        totalDaysAwake = totalDaysAwake + awakeTime[3]

    if args.seconds_since_last_wake_up:
        print(str(round(secondsSinceLastWakeUp)))
        sys.exit()

    print("\nWake/Sleep Time SystemD Journal Analyzer\n")
    print(" Boot under analysis: " + bootUnderAnalysis)
    print(" Initial Boot Timestamp: ", bootTime.strftime(defaultFormat), "\n")
    print(row_format.format(*headers))
    print(row_format.format(*rowSeparator))

    for row in matrix:
        print(row_format.format(*row))

    print(row_format.format(*rowSeparator), "\n")

    if shutdownTime is not None:
        print("Boot ended with a shutdown at "
              + shutdownTime.strftime(defaultFormat) + "\n")

    timeSinceBoot = calculateTimeDifference(lastTime, bootTime)
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
