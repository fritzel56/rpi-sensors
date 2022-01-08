# sds011 package from here: https://github.com/menschel/sds011
# Code below inspired by examples on that site
from sds011 import SDS011
import datetime as dt
import mqtt_helper as mh
import logging

logging.basicConfig(level=logging.WARNING)


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
    sds = SDS011(port=PORT, use_database=True)
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
    except KeyboardInterrupt:
        sds.__del__()
        logging.warning('closed')
