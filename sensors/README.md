# Context

This folder contains the code used to read data from my sensors, write them to a local database, and then forward them to the MQTT gateway. I used two sensors (so far) as part of this project:

1. The HY1361 to monitor ambient noise. Note this seems to be functionally the same as the WS1381.
2. The SDS011 to monitor particulate matter levels.

Not shown here is that there is also a folder within this folder called `data` which contains the local database where data is stored locally. The database is titled `measurements.db3` and contains to tables: db and measurements. These will need to exist for the code to run.

# File Guide


| File | Description |
|------|-------------|
| hy1361_runner.py | Code which reads from the HY1361 decibel sensor(huge thank you to mepster for all the work they did [here](https://github.com/mepster/wensn/blob/master/wensn.py)), writes to a local database, and forwards the data to an MQTT server. |
| mqtt_helper.py | Code used to compose and send messages to the MQTT server. |
| sds011_runner.py | Code which reads from the SDS011 particulate matter sensor (huge thank you to menschel for all the work they did [here](https://github.com/menschel/sds011)), writes to a local database, and forwards the data to an MQTT server. |
