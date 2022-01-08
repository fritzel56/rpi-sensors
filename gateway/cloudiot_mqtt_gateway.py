# Code from here:
# https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/cloud-iot-gateways-rpi/cloudiot_mqtt_gateway.py
'''
I added code so that it will reconnect after a disconnect
This turned out to be not terribly useful because
1. all messages associated with the last client will be lost
2. all devices need to reattach
Instead try changing the keep alive time for the connection?

other notes:
1. it does seem capable of keeping messages when wifi is down
   so long as it's back up before the keep alive ends but I have
   no idea how this works
2. the  GatewayState doesn't seem to work properly. never tracks pending_responses
    -> fixed by putting gateway_state.pending_responses[event_mid] = (client_addr, response)
        back in

Keep alive is coded in here:
https://github.com/eclipse/paho.mqtt.python/blob/master/src/paho/mqtt/client.py#L911
Can change it in our code by specifying another value when we call

You can see an example of keep alive being checked here:
https://github.com/eclipse/paho.mqtt.python/blob/master/src/paho/mqtt/client.py#L1633
does return rc = 1 which is not very helpful

actually this is probably the more valuable keep alive checker (as we always client._ping_t seems to stay 0 in my tests)
https://github.com/eclipse/paho.mqtt.python/blob/master/src/paho/mqtt/client.py#L2405

MQTT Topic is use for communication between the gateway device and Google's IoT server.
It then uses the MQTT topic to look up the appropriate Pub/Sub topic to publish to.
See notes here:
https://cloud.google.com/iot/docs/how-tos/devices#creating_a_device_registry_with_multiple_pubsub_topics
https://cloud.google.com/iot/docs/how-tos/mqtt-bridge#iot-core-mqtt-auth-run-python
'''



from __future__ import print_function

import argparse
import datetime
import datetime as dt
import os
import ssl
import time
import json
import socket
from time import ctime
import time

import jwt
import paho.mqtt.client as mqtt

HOST = ''
PORT = 10000
BUFSIZE = 2048
ADDR = (HOST, PORT)

udpSerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSerSock.setblocking(False)
udpSerSock.bind(ADDR)


class GatewayState:
    # This is the topic that the device will receive configuration updates on.
    mqtt_config_topic = ''

    # This is the topic that the device will receive configuration updates on.
    mqtt_error_topic = ''

    # Host the gateway will connect to
    mqtt_bridge_hostname = ''
    mqtt_bridge_port = 8883

    # for all PUBLISH messages which are waiting for PUBACK. The key is 'mid'
    # returned by publish().
    pending_responses = {}

    # SUBSCRIBE messages waiting for SUBACK. The key is 'mid' from Paho.
    pending_subscribes = {}

    # for all SUBSCRIPTIONS. The key is subscription topic.
    subscriptions = {}

    # Indicates if MQTT client is connected or not
    connected = False


gateway_state = GatewayState()


def create_jwt(project_id, private_key_file, algorithm, jwt_expires_minutes):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
    Args:
       project_id: The cloud project ID this device belongs to
       private_key_file: A path to a file containing either an RSA256 or
                       ES256 private key.
       algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
       jwt_expires_minutes: The time in minutes before the JWT expires.
    Returns:
        An MQTT generated from the given project_id and private key, which
        expires in 20 minutes. After 20 minutes, your client will be
        disconnected, and a new JWT will have to be generated.
    Raises:
        ValueError: If the private_key_file does not contain a known key.
    """

    token = {
      # The time that the token was issued at
      'iat': datetime.datetime.utcnow(),
      # The time the token expires.
      'exp':
      datetime.datetime.utcnow() +
      datetime.timedelta(minutes=jwt_expires_minutes),
      # The audience field should always be set to the GCP project id.
      'aud': project_id
    }

    # Read the private key file.
    with open(private_key_file, 'r') as f:
        private_key = f.read()

    print('Creating JWT using {} from private key file {}'.format(
        algorithm, private_key_file))

    return jwt.encode(token, private_key, algorithm=algorithm)
# [END iot_mqtt_jwt]


# [START iot_mqtt_config]
def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc))


def on_connect(client, unused_userdata, unused_flags, rc):
    """Callback for when a device connects."""
    print('on_connect', mqtt.connack_string(rc))

    gateway_state.connected = True

    # Subscribe to the config and error topics.
    client.subscribe(gateway_state.mqtt_config_topic, qos=1)
    client.subscribe(gateway_state.mqtt_error_topic, qos=0)


def on_disconnect(client, unused_userdata, rc):
    """Paho callback for when a device disconnects."""
    now = time.monotonic()
    print('now', now)
    print('last_msg_out', client._last_msg_out)
    print('last_msg_in', client._last_msg_in)
    dif = now - min(client._last_msg_out, client._last_msg_in)
    print('dif', dif)
    print('ping_t', client._ping_t)
    print(rc)
    print(client)
    print(unused_userdata)
    print('on_disconnect', error_str(rc))
    gateway_state.connected = False

    # re-connect
    # NOTE: should implement back-off here, but it's a tutorial
    # client.connect(gateway_state.mqtt_bridge_hostname, gateway_state.mqtt_bridge_port)


def on_publish(unused_client, userdata, mid):
    """Paho callback when a message is sent to the broker."""
    print('on_publish, userdata {}, mid {}'.format(userdata, mid))

    try:
        client_addr, message = gateway_state.pending_responses.pop(mid)
        message = str(message).encode('utf8')
        print('sending data over UDP {} {}'.format(client_addr, message))
        udpSerSock.sendto(message, client_addr)
        print('pending response count {}'.format(
                len(gateway_state.pending_responses)))
    except KeyError:
        print('Unable to find key {}'.format(mid))


def on_subscribe(unused_client, unused_userdata, mid, granted_qos):
    print('on_subscribe: mid {}, qos {}'.format(mid, granted_qos))


def on_message(unused_client, unused_userdata, message):
    """Callback when the device receives a message on a subscription."""
    payload = message.payload.decode('utf8')
    print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
            payload, message.topic, str(message.qos)))

    try:
        client_addr = gateway_state.subscriptions[message.topic]
        print('Relaying config[{}] to {}'.format(payload, client_addr))
        if payload == 'ON' or payload == b'ON':
            udpSerSock.sendto('ON'.encode('utf8'), client_addr)
        elif payload == 'OFF' or payload == b'OFF':
            udpSerSock.sendto('OFF'.encode('utf8'), client_addr)
        else:
            print('Unrecognized command: {}'.format(payload))
    except KeyError:
        print('Nobody subscribes to topic {}'.format(message.topic))


def get_client(
        project_id, cloud_region, registry_id, gateway_id, private_key_file,
        algorithm, ca_certs, mqtt_bridge_hostname, mqtt_bridge_port,
        jwt_expires_minutes):
    """Create our MQTT client. The client_id is a unique string that identifies
    this device. For Google Cloud IoT Core, it must be in the format below."""
    client = mqtt.Client(
        client_id=('projects/{}/locations/{}/registries/{}/devices/{}'.format(
            project_id,
            cloud_region,
            registry_id,
            gateway_id)))

    # With Google Cloud IoT Core, the username field is ignored, and the
    # password field is used to transmit a JWT to authorize the device.
    client.username_pw_set(
        username='unused',
        password=create_jwt(
            project_id, private_key_file, algorithm, jwt_expires_minutes))

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

    # Register callbacks. https://eclipse.org/paho/clients/python/docs/
    # describes additional callbacks that Paho supports. In this example,
    # the callbacks just print to standard out.
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    # Connect to the Google MQTT bridge.
    print('about to connect')
    try:
        client.connect(mqtt_bridge_hostname, mqtt_bridge_port)
    except:
        print('problem when trying to connect')
    print('connected')

    mqtt_topic = '/devices/{}/events'.format(gateway_id)
    client.publish(mqtt_topic, 'Gateway started.', qos=0)

    return client
# [END iot_mqtt_config]


def parse_command_line_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=(
        'Example Google Cloud IoT Core MQTT device connection code.'))
    parser.add_argument(
        '--project_id',
        default=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        help='GCP cloud project name')
    parser.add_argument(
        '--registry_id', required=True,
        help='Cloud IoT Core registry id')
    parser.add_argument(
        '--gateway_id', required=True, help='Cloud IoT Core gateway id')
    parser.add_argument(
        '--private_key_file',
        required=True, help='Path to private key file.')
    parser.add_argument(
        '--algorithm',
        choices=('RS256', 'ES256'),
        required=True,
        help='Which encryption algorithm to use to generate the JWT.')
    parser.add_argument(
        '--cloud_region', default='us-central1',
        help='GCP cloud region')
    parser.add_argument(
        '--ca_certs',
        default='roots.pem',
        help=('CA root from https://pki.google.com/roots.pem'))
    parser.add_argument(
        '--mqtt_bridge_hostname',
        default='mqtt.googleapis.com',
        help='MQTT bridge hostname.')
    parser.add_argument(
        '--mqtt_bridge_port',
        choices=(8883, 443),
        default=8883,
        type=int,
        help='MQTT bridge port.')
    parser.add_argument(
        '--jwt_expires_minutes',
        default=1200,
        type=int,
        help=('Expiration time, in minutes, for JWT tokens.'))

    return parser.parse_args()


# [START iot_mqtt_run]
def main():
    global gateway_state
    global skip_next_sub

    kickoff_time = dt.datetime.utcnow()

    print_time = dt.datetime.utcnow()
    messages=[]

    attached = []

    args = parse_command_line_args()

    gateway_state.mqtt_config_topic = '/devices/{}/config'.format(
            parse_command_line_args().gateway_id)
    gateway_state.mqtt_error_topic = '/devices/{}/errors'.format(
            parse_command_line_args().gateway_id)

    gateway_state.mqtt_bridge_hostname = args.mqtt_bridge_hostname
    gateway_state.mqtt_bridge_port = args.mqtt_bridge_hostname

    print('hi there')

    client = get_client(
        args.project_id, args.cloud_region, args.registry_id, args.gateway_id,
        args.private_key_file, args.algorithm, args.ca_certs,
        args.mqtt_bridge_hostname, args.mqtt_bridge_port,
        args.jwt_expires_minutes)

    print('hi there 2')

    i = 0
    # allow time for connection to succeed
    time.sleep(4)

    while True:
        # print(i)
        # print('another loop')
        if ((len(gateway_state.pending_responses) > 0) 
              and (((dt.datetime.utcnow() - print_time).seconds > 300) or messages != gateway_state.pending_responses)):
            messages = gateway_state.pending_responses
            print_time = dt.datetime.utcnow()
            print(print_time)
            print(gateway_state.pending_responses)
        # i=i+1
        #client.loop()

        if (((dt.datetime.utcnow() - kickoff_time).seconds > args.jwt_expires_minutes * 60 - 120)
                and len(gateway_state.pending_responses) == 0):
            print('refreshing the tokens at:')
            print(dt.datetime.now())

            client.disconnect()
            time.sleep(4)
            client = get_client(
                args.project_id, args.cloud_region, args.registry_id, args.gateway_id,
                args.private_key_file, args.algorithm, args.ca_certs,
                args.mqtt_bridge_hostname, args.mqtt_bridge_port,
                args.jwt_expires_minutes)
            print('reconnected')
            kickoff_time = dt.datetime.utcnow()
            time.sleep(4)
            #client.loop()
            for device_id in attached:
                print('Sending telemetry event for device {}'.format(device_id))
                attach_topic = '/devices/{}/attach'.format(device_id)
                auth = ''  # TODO:    auth = command["jwt"]
                attach_payload = '{{"authorization" : "{}"}}'.format(auth)

                print('Attaching device {}'.format(device_id))
                print(attach_topic)
                response, attach_mid = client.publish(
                        attach_topic, attach_payload, qos=1)

                message = template.format(device_id, 'attach')
                udpSerSock.sendto(message.encode('utf8'), client_addr)
                gateway_state.pending_responses[attach_mid] = (client_addr, response)

        client.loop()


        if gateway_state.connected is False:
            print('connect status {}'.format(gateway_state.connected))
            client = get_client(
                args.project_id, args.cloud_region, args.registry_id, args.gateway_id,
                args.private_key_file, args.algorithm, args.ca_certs,
                args.mqtt_bridge_hostname, args.mqtt_bridge_port,
                args.jwt_expires_minutes)
            print('reconnected')
            kickoff_time = dt.datetime.utcnow()
            time.sleep(4)
            #client.loop()
            for device_id in attached:
                print('Sending telemetry event for device {}'.format(device_id))
                attach_topic = '/devices/{}/attach'.format(device_id)
                auth = ''  # TODO:    auth = command["jwt"]
                attach_payload = '{{"authorization" : "{}"}}'.format(auth)

                print('Attaching device {}'.format(device_id))
                print(attach_topic)
                response, attach_mid = client.publish(
                        attach_topic, attach_payload, qos=1)

                message = template.format(device_id, 'attach')
                udpSerSock.sendto(message.encode('utf8'), client_addr)
                gateway_state.pending_responses[attach_mid] = (client_addr, response)

        #print('made it past if ' + str(i-1))
        


        try:
            data, client_addr = udpSerSock.recvfrom(BUFSIZE)
        except socket.error:
            continue
        print('[{}]: From Address {}:{} receive data: {}'.format(
                ctime(), client_addr[0], client_addr[1], data.decode("utf-8")))

        command = json.loads(data.decode('utf-8'))
        if not command:
            print('invalid json command {}'.format(data))
            continue

        action = command["action"]
        device_id = command["device"]
        template = '{{ "device": "{}", "command": "{}", "status" : "ok" }}'

        if action == 'event':
            print('Sending telemetry event for device {}'.format(device_id))
            payload = command["data"]

            sub_topic = command["sub_topic"]

            if sub_topic:
                mqtt_topic = '/devices/{}/events/{}'.format(device_id, sub_topic)
            else:
                mqtt_topic = '/devices/{}/events'.format(device_id)
            print(type(payload))
            print(payload)
            print('Publishing message to topic {} with payload \'{}\''.format(
                    mqtt_topic, payload))
            response, event_mid = client.publish(mqtt_topic, payload, qos=1)

            message = template.format(device_id, 'event')
            udpSerSock.sendto(message.encode('utf8'), client_addr)
            gateway_state.pending_responses[event_mid] = (client_addr, response)

        elif action == 'attach':
            if device_id not in attached:
                attached.append(device_id)
            print('Sending telemetry event for device {}'.format(device_id))
            attach_topic = '/devices/{}/attach'.format(device_id)
            auth = ''  # TODO:    auth = command["jwt"]
            attach_payload = '{{"authorization" : "{}"}}'.format(auth)

            print('Attaching device {}'.format(device_id))
            print(attach_topic)
            response, attach_mid = client.publish(
                    attach_topic, attach_payload, qos=1)

            message = template.format(device_id, 'attach')
            udpSerSock.sendto(message.encode('utf8'), client_addr)
            gateway_state.pending_responses[attach_mid] = (client_addr, response)
        elif action == 'detach':
            if device_id in attached:
                attached.remove(device_id)
            detach_topic = '/devices/{}/detach'.format(device_id)
            print(detach_topic)

            res, mid = client.publish(detach_topic, "{}", qos=1)

            message = template.format(res, mid)
            print('sending data over UDP {} {}'.format(client_addr, message))
            udpSerSock.sendto(message.encode('utf8'), client_addr)

        elif action == "subscribe":
            print('subscribe config for {}'.format(device_id))
            subscribe_topic = '/devices/{}/config'.format(device_id)
            skip_next_sub = True

            _, mid = client.subscribe(subscribe_topic, qos=1)
            message = template.format(device_id, 'subscribe')
            gateway_state.subscriptions[subscribe_topic] = client_addr

            udpSerSock.sendto(message.encode('utf8'), client_addr)

        else:
            print('undefined action: {}'.format(action))

    print('Finished.')


if __name__ == '__main__':
    main()
