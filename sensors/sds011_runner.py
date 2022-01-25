# sds011 package from here: https://github.com/menschel/sds011
# Code below inspired by examples on that site
from sds011 import SDS011
import datetime as dt
import mqtt_helper as mh
import logging
import sqlite3
import sys

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.WARNING)


def write_to_db(measurement, table):
    db3path = "measurements.db3"
    conn = sqlite3.connect(db3path)
    c = conn.cursor()
    logging.info('connected to database')
    try:
        linedata = [measurement.get(x) for x in ["timestamp","pm2.5","pm10","devid"]]
        c.execute("insert into {0} (timestamp,pm2_5,pm10,devid) values (?,?,?,?)".format(table),linedata)
        conn.commit()
        conn.close()
    except Exception:
        conn.close()
        err = sys.exc_info()
        err_message = traceback.format_exception(*err)
        err_str = '<br>'.join(err_message)
        err_str = err_str.replace('\n', '')
        issue = "Issue writing to database: <br> {}".format(err_str)
        logging.warning(issue)


if __name__ == '__main__':
    # set basic device infro
    device_id = 'SDS011'
    location = 2
    
    # ensure device is connected to the server
    response = mh.send(device_id, 'detach', '')
    logging.info(f'detach response: {response}')
    response = mh.send(device_id, 'attach', '')
    logging.info(f'attach response: {response}')
    
    # set up connection to device
    PORT = "/dev/ttyUSB0"
    sds = SDS011(port=PORT)
    sds.set_data_reporting('active')
    sds.set_working_period(rate=10)
    logging.info(sds)
    try:
        while True:
            measurement = sds.read_measurement()
            values = [measurement.get(key) for key in ["timestamp", "pm2.5", "pm10", "device_id"]]
            logging.info(measurement)
            # encode timestamp to int for easy writing
            timestamp = int(values[0].timestamp())
            data = {'Date': timestamp, 'pm2_5': values[1], 'pm10': values[2], 'device_id': values[3], 'loc': location}
            data = str([data])
            mh.send(device_id, 'event', data, 'SDS011')
            write_to_db(measurement, "measurements")
    except KeyboardInterrupt:
        sds.__del__()
        logging.warning('keyboard interrupt: gracefully exited')
    except Exception:
        err = sys.exc_info()
        err_message = traceback.format_exception(*err)
        err_str = '<br>'.join(err_message)
        err_str = err_str.replace('\n', '')
        issue = "Issue writing to database: <br> {}".format(err_str)
        sds.__del__()
        logging.warning('New error. Executing graceful shutdown. Details as follows:')
        logging.warning(issue)
