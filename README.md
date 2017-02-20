# lastwake.py
Wake/Suspend Time SystemD Journal Analyzer [current boot]

Sample Output:

```
Wake/Suspend Time SystemD Journal Analyzer [current boot]

Initial Boot Timestamp:  2017-02-19 13:05:47 

    Wake Timestamp    |  Suspend Timestamp   |      Awake Time      |   Wake Type    |
 -------------------- | -------------------- | -------------------- | -------------- |
 2017-02-19 13:05:47  | 2017-02-19 13:11:47  |         0h  5m       |   Cold Boot    |
 2017-02-19 13:12:51  | 2017-02-19 13:59:16  |         0h 46m       | S4 (from disk) |
 2017-02-19 20:43:29  | 2017-02-19 20:54:51  |         0h 11m       | S4 (from disk) |
 2017-02-19 20:55:07  | 2017-02-19 23:43:07  |         2h 47m       | S3 (from RAM)  |
 2017-02-19 23:43:38  |    (Still Awake)     |         0h 23m       | S3 (from RAM)  |
 -------------------- | -------------------- | -------------------- | -------------- | 

Summary: Days Since Boot [0.46] | Days Awake [0.18] | Suspend/Wake Cycles: [4]

```

