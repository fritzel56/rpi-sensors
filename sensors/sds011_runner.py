# sds011 package from here: https://github.com/menschel/sds011
# Code below inspired by examples on that site
from sds011 import SDS011
import datetime as dt
import mqtt_helper as mh
import logging
import sqlite3
import sys


logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.WARNING)


def write_to_db(measurement, conn, table):
    c = conn.cursor()
    linedata = [measurement.get(x) for x in ["timestamp","pm2.5","pm10","devid"]]
    c.execute("insert into {0} (timestamp,pm2_5,pm10,devid) values (?,?,?,?)".format(table),linedata)
    conn.commit()
    conn.close()


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
    
    # database info
    table = "measurements"
    db3path = "measurements.db3"
    while True:
        try:
            # set up db connection
            conn = sqlite3.connect(db3path)
            logging.info('connected to database')
            
            # get measurements and write
            measurement = sds.read_measurement()
            values = [measurement.get(key) for key in ["timestamp", "pm2.5", "pm10", "device_id"]]
            logging.info(measurement)
            # encode timestamp to int for easy writing
            timestamp = int(values[0].timestamp())
            data = {'Date': timestamp, 'pm2_5': values[1], 'pm10': values[2], 'device_id': values[3], 'loc': location}
            data = str([data])
            mh.send(device_id, 'event', data, 'SDS011')
            write_to_db(measurement, conn, table)
        except KeyboardInterrupt:
            sds.__del__()
            conn.close()
            logging.error('keyboard interrupt: gracefully exited')
            sys.exit(1)
        except sqlite3.OperationalError:
            conn.close()
            logging.warning('Issue writing to database. Details as follows:', exc_info=True)
        except Exception:
            sds.__del__()
            conn.close()
            logging.error('New error. Executing graceful shutdown. Details as follows:', exc_info=True)
            sys.exit(1)
