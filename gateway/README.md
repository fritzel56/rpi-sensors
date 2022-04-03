# Context
This folder contains code used to setup and run the MQTT gateway. The code comes from [this google repo](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/cloud-iot-gateways-rpi/cloudiot_mqtt_gateway.py).

For this code to run, you will need the following environment variables to be set:

```
registry_id
gateway_id
project_id
ca_certs
private_key_file
```

# File Guide
| File | Description |
|------|-------------|
| cloudiot_mqtt_gateway.py | Actual logic to host the gateway. |
| roots.pem and rsa_public.pem and rsa_private.pem | Files used to connect to Google Core IoT. Not actually commited to git.  For details on how to set these up, see [here](https://cloud.google.com/community/tutorials/cloud-iot-gateways-rpi). |
| run-gateway | Code to run in terminal to run the server. |
