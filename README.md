# lastwake.py
Wake/Sleep Time SystemD Journal Analyzer [current boot]

What it does: Analyzes the system journal and prints out wake-up and sleep timestamps; for each cycle it tells whether the system was suspended to RAM or to disk (hibernated).

Sample Output:

```
Wake/Sleep Time SystemD Journal Analyzer [current boot]

Initial Boot Timestamp:  2017-02-20 09:22:17 

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

