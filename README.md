

# lastwake.py
Wake/Sleep Time SystemD Journal Analyzer

**What it does:** Analyzes the system journal and prints out wake-up and sleep timestamps; for each cycle it tells whether the system was suspended to RAM or to disk (hibernated).

By default it will perform the analysis of wake-up/sleep cycles for the current boot, but also accepts a boot-id as an arguments (boot-id's can be obtained from: journalctl --list-boots)


## Requirements
This program requires:

1. The `libsystemd` development library. To get it:

    In recent ubuntu versions:
    ```
    sudo apt install libsystemd-dev
    ```
    In fedora:
    ```
    sudo dnf install systemd-devel
    ```
  
1. And finally: `systemd-python` ([Github](https://github.com/systemd/python-systemd), [PyPI](https://pypi.python.org/pypi/systemd-python)). To get it:

    ```
    pip3 install -r requirements.txt
    ```


## Installation
1. Install the requirements above.
1. Create a symbolic link to the program in your **"~/bin"** dir:
    ```bash
    # create the ~/bin dir if it doesn't already exist
    mkdir -p ~/bin
    # change to this repository's "lastwake.py" **directory**
    cd path/to/lastwake.py
    # Create a symbolic link, named `lastwake`, to the Python executable inside the ~/bin dir
    ln -si "${PWD}/lastwake.py" ~/bin/lastwake
    ```
1. On Ubuntu, if this is the first time creating and using the ~/bin dir, log out and log back in to automatically add this dir to your PATH. If on another Linux system, do what is required to add the ~/bin dir to your PATH variable. Now you can call `lastwake` from anywhere in your terminal.


## Usage

    lastwake [-h] [-b BOOT_ID] [-s] [bootId]


### Examples

    lastwake

    lastwake --boot-id afdffb7dae61404abb5506ebf10ee2ac

    lastwake afdffb7dae61404abb5506ebf10ee2ac


## Sample Output

### Current boot

```
Wake/Sleep Time SystemD Journal Analyzer

 Boot under analysis: current boot
 Initial Boot Timestamp:  2026-08-26 00:56:51 

   Wake Timestamp    |   Sleep Timestamp   | Awake Time | Wake From
 ------------------- | ------------------- | ---------- | ---------
 2026-08-26 00:56:51 | 2026-08-26 01:33:12 |    0h 36m  | S5 (boot)
 2026-08-26 20:31:01 | 2026-08-26 22:27:07 |    1h 56m  | S4 (disk)
 2026-08-27 02:27:18 | 2026-08-27 02:30:03 |    0h  2m  | S3 (RAM) 
 2026-08-27 20:09:02 | 2026-08-27 21:09:45 |    1h  0m  | S4 (disk)
 2026-08-27 21:34:46 | 2026-08-27 22:23:38 |    0h 48m  | S3 (RAM) 
 2026-08-28 00:42:01 | 2026-08-31 09:16:51 |   80h 34m  | S3 (RAM) 
 2026-09-05 13:24:40 |    (Still Awake)    |   35h 31m  | S4 (disk)
 ------------------- | ------------------- | ---------- | --------- 

Days Since Boot: 12.00 - Days Awake: 5.02 - Wake/Sleep Cycles: 6
```

### Prior boot

```
lastwake -b -1

Wake/Sleep Time SystemD Journal Analyzer

 Boot under analysis: selected boot = 6dc1e33ad56641dba43ca10b4bf45c65
 Initial Boot Timestamp:  2026-08-11 20:11:26 

   Wake Timestamp    |   Sleep Timestamp   | Awake Time | Wake From
 ------------------- | ------------------- | ---------- | ---------
 2026-08-11 20:11:26 | 2026-08-11 21:34:36 |    1h 23m  | S5 (boot)
 2026-08-12 00:29:21 | 2026-08-12 02:00:37 |    1h 31m  | S3 (RAM) 
 2026-08-12 20:11:26 | 2026-08-13 01:33:31 |    5h 22m  | S4 (disk)
 2026-08-13 20:13:34 | 2026-08-14 00:59:15 |    4h 45m  | S4 (disk)
 2026-08-14 19:37:52 | 2026-08-14 22:11:14 |    2h 33m  | S4 (disk)
 2026-08-15 02:11:25 | 2026-08-15 02:14:03 |    0h  2m  | S3 (RAM) 
 2026-08-15 11:18:54 | 2026-08-15 12:56:07 |    1h 37m  | S4 (disk)
 2026-08-15 13:19:08 | 2026-08-15 20:48:24 |    7h 29m  | S3 (RAM) 
 2026-08-16 00:48:35 | 2026-08-16 00:51:03 |    0h  2m  | S3 (RAM) 
 2026-08-16 11:29:43 | 2026-08-16 14:50:28 |    3h 20m  | S4 (disk)
 2026-08-16 18:50:39 | 2026-08-16 18:53:02 |    0h  2m  | S3 (RAM) 
 2026-08-17 19:26:33 | 2026-08-17 20:48:55 |    1h 22m  | S4 (disk)
 2026-08-18 00:18:03 | 2026-08-18 01:54:30 |    1h 36m  | S3 (RAM) 
 2026-08-18 20:06:14 | 2026-08-18 21:26:12 |    1h 19m  | S4 (disk)
 2026-08-18 23:58:31 | 2026-08-19 02:42:29 |    2h 43m  | S3 (RAM) 
 2026-08-19 18:23:38 | 2026-08-19 19:30:21 |    1h  6m  | S4 (disk)
 2026-08-19 20:30:07 | 2026-08-19 21:25:10 |    0h 55m  | S3 (RAM) 
 2026-08-20 01:25:21 | 2026-08-20 01:28:03 |    0h  2m  | S3 (RAM) 
 2026-08-20 01:30:01 | 2026-08-20 02:02:31 |    0h 32m  | S4 (disk)
 2026-08-20 02:02:50 | 2026-08-20 02:03:16 |    0h  0m  | S3 (RAM) 
 2026-08-21 00:09:19 | 2026-08-21 01:52:47 |    1h 43m  | S4 (disk)
 2026-08-21 19:51:56 | 2026-08-21 21:31:56 |    1h 40m  | S4 (disk)
 2026-08-22 01:32:07 | 2026-08-22 01:35:03 |    0h  2m  | S3 (RAM) 
 2026-08-22 11:33:19 | 2026-08-22 18:05:29 |    6h 32m  | S4 (disk)
 2026-08-22 18:18:40 | 2026-08-22 18:23:08 |    0h  4m  | S3 (RAM) 
 2026-08-22 22:23:18 | 2026-08-22 22:26:03 |    0h  2m  | S3 (RAM) 
 2026-08-23 10:30:14 | 2026-08-23 11:36:59 |    1h  6m  | S4 (disk)
 2026-08-23 14:52:07 | 2026-08-24 00:47:30 |    9h 55m  | S3 (RAM) 
 2026-08-24 19:49:23 | 2026-08-24 21:14:28 |    1h 25m  | S4 (disk)
 2026-08-25 01:09:14 | 2026-08-25 02:38:42 |    1h 29m  | S3 (RAM) 
 2026-08-25 23:42:37 | 2026-08-26 00:55:58 |    1h 13m  | S4 (disk)
 ------------------- | ------------------- | ---------- | --------- 

Boot ended with a shutdown at 2026-08-26 00:55:58

Days Since Boot: 14.20 - Days Awake: 2.63 - Wake/Sleep Cycles: 30
```

### Server Use-Case: how many days between restarts, 3 boots ago
```
lastwake -b -3

Wake/Sleep Time SystemD Journal Analyzer

 Boot under analysis: selected boot = d1709d4ce5ea40a2b10d39b4dd1dfb28
 Initial Boot Timestamp:  2026-05-23 14:50:29 

   Wake Timestamp    |   Sleep Timestamp   | Awake Time | Wake From
 ------------------- | ------------------- | ---------- | ---------
 2026-05-23 14:50:29 | 2026-07-10 22:50:36 | 1160h  0m  | S5 (boot)
 ------------------- | ------------------- | ---------- | --------- 

Boot ended with a shutdown at 2026-07-10 22:50:36

Days Since Boot: 48.33 - Days Awake: 48.33 - Wake/Sleep Cycles: 0
```

