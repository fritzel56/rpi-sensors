# simple functions used to help my devices communicate with the MQTT bridge
# code inspired by code here:
# https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/cloud-iot-gateways-rpi/thermostat.py

import socket

def make_message(device_id, action, data='', sub_topic=''):
    """Takes in various device paraments and returns a message to be passed to the MQTT server.

    Args:
        devide_id(str): ID associated with the device (in this case as registered in Google IOT core).
        action(str): type of action associated with the message (ex: attach, detach, event)
        data(dict): if an event, data to be transmitted
        sub_topic(str): used to route the message once it arrives at Google IOT core

    Returns:
        dict: formatted message to send to the MQTT server
    """
    if data:
        return '{{ "device" : "{}", "action":"{}", "data" : "{}", "sub_topic" : "{}" }}'.format(
            device_id, action, data, sub_topic)
    else:
        return '{{ "device" : "{}", "action":"{}" }}'.format(device_id, action)


def send(device_id, action, data='', sub_topic=''):
    """ Sets up connection, composes message, sends message.

    Args:
        devide_id(str): ID associated with the device (in this case as registered in Google IOT core).
        action(str): type of action associated with the message (ex: attach, detach, event)
        data(dict): if an event, data to be transmitted
        sub_topic(str): used to route the message once it arrives at Google IOT core
    """
    # server details
    addr = 'localhost'
    port = 10000
    
    # Create a UDP socket
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (addr, port)
    
    # Compose message
    message = make_message(device_id, action, data, sub_topic)
    
    # Send message
    client_sock.sendto(message.encode('utf8'), server_address)
