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


## Usage

    lastwake [-h] [-b BOOT_ID] [bootId]


### Examples

    lastwake

    lastwake --boot-id afdffb7dae61404abb5506ebf10ee2ac

    lastwake afdffb7dae61404abb5506ebf10ee2ac


## Sample Output

```
Wake/Sleep Time SystemD Journal Analyzer

 Boot under analysis: selected boot = afdffb7dae61404abb5506ebf10ee2ac
 Initial Boot Timestamp:  2017-07-06 11:23:42

   Wake Timestamp    |   Sleep Timestamp   | Awake Time | Wake From
 ------------------- | ------------------- | ---------- | ---------
 2017-02-20 09:22:17 | 2017-02-20 09:52:18 |    0h 30m  | Cold Boot
 2017-02-20 10:27:13 | 2017-02-20 10:49:26 |    0h 22m  | S4 (disk)
 2017-02-20 10:50:50 | 2017-02-20 11:03:16 |    0h 12m  | S4 (disk)
 2017-02-20 21:51:55 | 2017-02-20 22:41:44 |    0h 49m  | S4 (disk)
 2017-02-20 22:42:10 |    (Still Awake)    |    0h  1m  | S3 (RAM) 
 ------------------- | ------------------- | ---------- | --------- 

Days Since Boot: 0.51 - Days Awake: 0.09 - Wake/Sleep Cycles: 4
```
