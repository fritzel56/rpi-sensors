# code from here: https://github.com/mepster/wensn/blob/master/wensn.py
import usb.core
import datetime as dt
import mqtt_helper as mh
import time
import sqlite3
import logging
import sys
import traceback
import email_helpers as eh

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.WARNING)

# Device information
LOCATION = 3
DEVICEID = 'WS1361-decibel-meter'

# HY1361 settings
RANGES = ["30-80", "40-90", "50-100", "60-110", "70-120", "80-130", "30-130"]
SPEEDS = ["fast", "slow"]
WEIGHTS = ["A", "C"]


def write_to_db(measurement, conn, table):
    c = conn.cursor()
    # use write ahead logging
    c.execute('PRAGMA journal_mode=wal')
    c.execute("insert into {0} (db, range, weight, speed, location, measurement_ts) values (?,?,?,?,?,?)".format(table), measurement)
    conn.commit()
    conn.close()


def connect():
    """Finds the device's USB info and returns relevant info.
    
    Returns:
        usb.core.Device: info which port device is connected to
    """
    dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc)
    assert dev is not None
    logging.debug(dev)
    return dev


def readSPL(dev):
    """Reads data from HY1361
    
    Args:
        dev(usb.core.Device): connection details for the device
    Returns:
        tuple: data read from the device
    """
    ret = dev.ctrl_transfer(0xC0, 4, 0, 10, 200) # wvalue (3rd arg) is ignored
    rangeN = (ret[1]&28)>>2 # bits 2,3,4 in ret[1] return rangeN from 0 to 6
    weightN = (ret[1]&32)>>5 # bit 5 in ret[1] return weightN
    speedN = (ret[1]&64)>>6 # bit 6 in ret[1] return speedN
    dB = (ret[0] + ((ret[1] & 3) * 256)) * 0.1 + 30
    return(dB, RANGES[rangeN], WEIGHTS[weightN], SPEEDS[speedN])


if __name__ == '__main__':
    logging.info('started up')
    # connect to MQTT gateway
    response = mh.send(DEVICEID, 'detach', '')
    logging.info(f'detach response: {response}')
    response = mh.send(DEVICEID, 'attach', '')
    logging.info(f'attach response: {response}')
    logging.info('connected to gateway')
    
    # connect to device
    dev = connect()
    logging.info('connected to device')

    data_list = []
    
    # database info
    table = "db"
    db3path = "data/measurements.db3"

    while True:
        try:
            logging.debug('started another loop')
            
            # set up db connection
            conn = sqlite3.connect(db3path)
            logging.info('connected to database')
            
            # Read and format data
            values = list(readSPL(dev))
            now = dt.datetime.now()
            now_ts = int(now.timestamp())
            data = {'db': values[0], 'r': values[1], 'w': values[2], 's': values[3], 'l': LOCATION, 'Date': now_ts}
            data_list.append(data)
            
            # bundle readings to lower the number of messages sent to stay in free zone
            # send to server once there are 11 of them
            if len(data_list) >= 11:
                data_list = str(data_list)
                mh.send(DEVICEID, 'event', data_list, 'WS1361')
                data_list = []
            
            # write to local database
            values.append(LOCATION)
            values.append(now)
            write_to_db(values, conn, table)
            
            # sleep until next reading
            time.sleep(2)
        except KeyboardInterrupt:
            conn.close()
            logging.error('keyboard interrupt: gracefully exited')
            sys.exit(1)
        except sqlite3.OperationalError:
            conn.close()
            logging.warning('Issue writing to database. Details as follows:', exc_info=True)
        except usb.core.USBError:
            logging.warning('Issue reading from device. Reconnecting. Details as follows:', exc_info=True)
            dev = connect()
            logging.warning('Reconnected')
        except Exception:
            conn.close()
            logging.error('New error. Executing graceful shutdown. Details as follows:', exc_info=True)
            
            # send email alert
            subject = 'Unexpected Error with HY1361'
            err = sys.exc_info()
            err_message = traceback.format_exception(*err)
            err_str = '<br>'.join(err_message)
            err_str = err_str.replace('\n', '')
            body = 'New error for HY1361. Process is shutting down and data will stop recording. Details as follows: <br> {}'.format(err_str)
            email = eh.email_composition(subject, body)
            eh.send_email(email)
            
            # close the program
            sys.exit(1)