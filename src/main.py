"""
Copyright 2022 Rob Weber
This file is part of ha-betabrite-sign
omni-epd is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import configargparse
import json
import logging
import signal
import sys
import threading
import time
import alphasign
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as mqtt_subscribe
from datetime import datetime, timedelta
from slugify import slugify
from termcolor import colored
from lib.manager import MessageManager, PayloadManager
from lib.home_assistant import HomeAssistant
from lib import constants

# create global vars
active_queue = "main"  # default active queue at startup
betabrite = None
manager = None
mqtt_client = None
payload_manager = None
thread_lock = threading.Lock()  # ensure exclusive access to betabrite serial port


def signal_handler(signum, frame):
    """function to handle when the is killed and exit gracefully"""
    logging.debug('Exiting Program')

    if(mqtt_client is not None):
        # publish we're going offline
        mqtt_client.publish(constants.MQTT_AVAILABLE, "offline", retain=True)

        # disconnect
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

    sys.exit(0)


def mqtt_connect(client, userdata, flags, rc):
    """run on successful mqtt connection"""
    logging.info("Connected to MQTT Server")

    device_name_slug = slugify(args.ha_device_name, separator='_')
    discovery_topics = {constants.MQTT_DISCOVERY_LIGHT_CLASS: "", constants.MQTT_DISCOVERY_TEXT_CLASS: ""}
    if(args.ha_discovery):

        # device config
        ha_device = {"name": args.ha_device_name, "identifiers": device_name_slug,
                     "sw_version": constants.PROJECT_VERSION, "manufacturer": "Rob Weber"}

        # generate the light entity config https://www.home-assistant.io/integrations/light.mqtt/
        discovery_topics[constants.MQTT_DISCOVERY_LIGHT_CLASS] = {"name": f"{args.ha_device_name} Light", "device_class": constants.MQTT_DISCOVERY_LIGHT_CLASS,  # noqa
                                                                  "object_id": device_name_slug, "unique_id": f"{device_name_slug}_light", "state_topic": constants.MQTT_STATUS,  # noqa
                                                                  "command_topic": constants.MQTT_SWITCH, "json_attributes_topic": constants.MQTT_ATTRIBUTES,  # noqa
                                                                  "availability_topic": constants.MQTT_AVAILABLE, "qos": 0, "payload_on": "ON", "payload_off": "OFF", # noqa
                                                                  "color_mode": True, "supported_color_modes": ["onoff"], "optimistic": False, "device": ha_device} # noqa

        # generate the text config https://www.home-assistant.io/integrations/text.mqtt/
        discovery_topics[constants.MQTT_DISCOVERY_TEXT_CLASS] = {"name": f"{args.ha_device_name} Text", "device_class": constants.MQTT_DISCOVERY_TEXT_CLASS,  # noqa
                                                                 "object_id": f"{device_name_slug}_text", "unique_id": f"{device_name_slug}_text",
                                                                 "state_topic": constants.MQTT_CURRENT_TEXT, "command_topic": constants.MQTT_NEW_TEXT,
                                                                 "availability_topic": constants.MQTT_AVAILABLE, "qos": 0, "device": ha_device}

    for entity_type in discovery_topics:
        topic = f"{args.mqtt_discovery_prefix}/{entity_type}/{device_name_slug}/config"

        if(args.ha_discovery):
            # publish the entity config to the HA discovery prefix
            logging.debug(f"Configuring HA Entity {topic}: {json.dumps(discovery_topics[entity_type])}")
            mqtt_client.publish(topic, json.dumps(discovery_topics[entity_type]), retain=True)
        else:
            # publish blank string to delete the device
            mqtt_client.publish(topic, "", retain=True)


def mqtt_on_message(client, userdata, message):
    """triggered when message is received via mqtt"""
    logging.debug(colored(message.topic, 'red') + " " + str(message.payload))

    if(message.topic == constants.MQTT_SWITCH):
        change_state(str(message.payload.decode('utf-8')))

        # publish new status and any attributes
        mqtt_client.publish(constants.MQTT_STATUS, message.payload, retain=True)
        mqtt_publish_attributes()

    elif(message.topic == constants.MQTT_COMMAND):
        # format is {command:"", params: {}}  noqa: E800
        payload = json.loads(message.payload.decode('utf-8'))

    elif(message.topic == constants.MQTT_NEW_TEXT):
        # republish into state topic
        mqtt_client.publish(constants.MQTT_CURRENT_TEXT, message.payload, retain=True)

    else:
        # this is for a variable, load it
        aVar = manager.get_variable_by_filter(constants.MQTT_CATEGORY, lambda v: v.get_topic() == message.topic)

        if(aVar is not None):
            payload = str(message.payload.decode('utf-8'))

            # decode if payload is json
            if(constants.is_json(payload)):
                payload = json.loads(payload)

            # save the new payload
            payload_manager.set_payload(aVar.get_name(), payload)

            # render this variable
            render_template(aVar)

            # re-render any dependant variables
            for dep in payload_manager.get_dependencies(aVar.get_name()):
                render_template(manager.get_variable_by_name(dep))


def mqtt_publish_attributes():
    # make sure MQTT is setup
    if(mqtt_client is not None):
        attributes = {"last_updated": str(datetime.now().astimezone().isoformat(timespec='seconds')),
                      "active_queue": active_queue,
                      "device_ip": constants.get_local_ip()}

        mqtt_client.publish(constants.MQTT_ATTRIBUTES,
                            json.dumps(attributes),
                            retain=True)


def render_template(var):
    """Render the Jinja variable and update the sign"""
    if(payload_manager.should_update(var)):
        # render the template
        newString = payload_manager.render_variable(var)

        if(newString is not None):
            # update the data on the sign if text has changed
            update_string(var.get_name(), newString)
    else:
        logging.debug(f"update conditional not met for {var.get_name()}")


def setup():
    """Setup the sign by allocating memory for variables and messages"""
    # connect to the sign and clear any data
    betabrite.connect()
    betabrite.clear_memory()

    # wait for sign to clear memory
    time.sleep(2)

    messages = manager.startup(betabrite)

    logging.info('allocating and sending run sequence')

    betabrite.allocate(tuple(messages['allocate']))
    betabrite.set_run_sequence(tuple(messages['run']))

    # write each object to the sign
    for obj in messages['allocate']:
        betabrite.write(obj)

    betabrite.disconnect()

    logging.info(f"loading message queue: {colored('main', 'yellow')}")


def poll(offset=timedelta(minutes=1)):
    """Gets all polling type variables and checks if they need updating

    :param offset: the offset to use when calculating the next update time, 1 min is the default otherwise the next time will never happen
    """
    # get all polling type variables that need to be updated
    now = datetime.now()
    pollingVars = manager.get_variables_by_filter(constants.POLLING_CATEGORY, lambda v: v.should_poll(now, offset))

    # load the HA interface, if needed
    homeA = None
    if(args.ha_url and args.ha_token):
        homeA = HomeAssistant(args.ha_url, args.ha_token)

    for v in pollingVars:
        logging.info(f"Polling {v.get_name()}")

        # update based on the type
        newString = None
        if(v.get_type() == 'date'):
            newString = v.get_text()
        elif(v.get_type() == 'rest'):
            # attempt to get new data
            payload = v.poll()

            # decode if payload is json
            if(constants.is_json(payload)):
                payload = json.loads(payload)

            # save the new payload
            payload_manager.set_payload(v.get_name(), payload)

            # render this variable
            render_template(v)

            # re-render any dependant variables
            for dep in payload_manager.get_dependencies(v.get_name()):
                render_template(manager.get_variable_by_name(dep))

        elif(v.get_type() == 'dynamic'):
            # render this variable
            render_template(v)
        elif(v.get_type() == 'home_assistant'):
            if(homeA is not None):
                try:
                    # render the template in home assistant, save the result
                    newString = homeA.render_template(v.get_text()).strip()
                    payload_manager.set_payload(v.get_name(), newString)
                except Exception as ex:
                    logging.error(ex)

            else:
                logging.error("Home Assistant interface is not loaded, specify HA url and token to load")

        if(newString is not None):
            update_string(v.get_name(), newString)


def change_state(newState):
    """changes the state of the sign on or off
    this is called when triggered via the MQTT_SWITCH topic

    :param newState: the new state of the sign (ON/OFF)
    """
    thread_lock.acquire()
    betabrite.connect()

    # create the sign object and update the sign
    if(newState == 'OFF'):
        offMessage = manager.update_text(constants.SIGN_OFF, ' ', True)
    else:
        offMessage = manager.update_text(constants.SIGN_OFF, '', True)

    betabrite.write(offMessage)
    betabrite.disconnect()
    thread_lock.release()


def find_active_queue():
    """finds the active queue based on the rules defined in the config file
    and swaps the queue if necessary
    """
    global active_queue
    new_queue = manager.find_active_queue(payload_manager)

    # swap the queue if it's not the current one
    if(new_queue != active_queue):
        queue_list = manager.get_queue(new_queue)

        thread_lock.acquire()
        betabrite.connect()

        # set the new run sequence
        betabrite.set_run_sequence(tuple(queue_list))
        logging.info(f"loading message queue: {colored(new_queue, 'yellow')}")

        betabrite.disconnect()
        thread_lock.release()

        # save the new queue name
        active_queue = new_queue
        mqtt_publish_attributes()


def update_string(name, msg):
    """Update a string object on the sign

    :param name: the name of the string to update, as defined in the yaml config
    :param msg: the message to send to the sign
    """
    # replace some chars
    msg = msg.replace('_', ' ')

    strObj = manager.update_string(name, msg)

    # write to sign if this String exists
    if(strObj is not None):
        logging.debug(f"updated {name}:'{colored(constants.strip_control(msg), 'green')}'")
        thread_lock.acquire()
        betabrite.connect()

        betabrite.write(strObj)

        betabrite.disconnect()
        thread_lock.release()
    else:
        logging.debug(f"can't find allocated object for {name}")


# parse the arguments
parser = configargparse.ArgumentParser(description='Home Assistant Betabrite Sign')
parser.add_argument('-c', '--config', is_config_file=True,
                    help='Path to custom config file')
parser.add_argument('-l', '--layout', default="data/layout.yaml",
                    help="Path to yaml file containing sign text layout, default is %(default)s")
parser.add_argument('-d', '--device', default="/dev/ttyUSB0",
                    help="Path to device where Alphasign is connected, default is %(default)s, can also use 'cli' to output to screen only")
parser.add_argument('-D', '--debug', action='store_true',
                    help='Enables logging debug mode')

# ha polling args
haGroup = parser.add_argument_group("Home Assistant", "Settings required for Home Assistant polling")
haGroup.add_argument('--ha_url', required=False,
                     help="Home Assistant full base url")
haGroup.add_argument('--ha_token', required=False,
                     help="Home Assistant Access Token")

# MQTT args
mqttGroup = parser.add_argument_group("MQTT", "Settings required for MQTT integrations")
mqttGroup.add_argument('-m', '--mqtt', required=False,
                       help="MQTT Server IP")
mqttGroup.add_argument('--mqtt_username', required=False,
                       help="MQTT Server username")
mqttGroup.add_argument('--mqtt_password', default=None, required=False,
                       help="MQTT Server password")
mqttGroup.add_argument('--ha_discovery', action='store_true',
                       help="Enable Home Assistant MQTT Discovery, default is False")
mqttGroup.add_argument('--ha_device_name', default="Betabrite Sign",
                       help="The Home Assistant entity name, default is '%(default)s'")
mqttGroup.add_argument('--mqtt_discovery_prefix', default="homeassistant",
                       help="The Home Assistant MQTT Discovery Prefix, default is '%(default)s'")

args = parser.parse_args()

# add hooks for interrupt signal
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# setup the logger, log to sign.log
logLevel = 'INFO' if not args.debug else 'DEBUG'
logHandlers = [logging.FileHandler('sign.log')]

if(args.debug):
    logHandlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(datefmt='%m/%d %H:%M',
                    format="%(levelname)s %(asctime)s: %(message)s",
                    level=getattr(logging, logLevel),
                    handlers=logHandlers)

logging.debug('Debug Mode On')

logging.info(f"Starting Home Assistant Betabrite Sign - Version {constants.PROJECT_VERSION}")

if(args.device == 'cli'):
    logging.info('Outputting sign info to CLI')
    betabrite = alphasign.interfaces.local.DebugInterface()
else:
    betabrite = alphasign.interfaces.local.Serial(device=args.device)

logging.info("Loading layout: " + args.layout)
manager = MessageManager(args.layout)

setup()

# sleep for a few seconds
time.sleep(10)

# setup the payload manager
payload_manager = PayloadManager(manager.get_variables_by_filter(constants.JINJA_CATEGORY))

if(args.mqtt and args.mqtt_username):

    # get the last known status from MQTT
    statusMsg = mqtt_subscribe.simple(constants.MQTT_STATUS, hostname=args.mqtt,
                                      auth={"username": args.mqtt_username, "password": args.mqtt_password})
    logging.info(f"Startup state is: {colored(str(statusMsg.payload.decode('utf-8')), 'yellow')}")
    change_state(str(statusMsg.payload.decode('utf-8')))

    # setup the MQTT connection
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(args.mqtt_username, args.mqtt_password)

    # set the callback methods
    mqtt_client.on_connect = mqtt_connect
    mqtt_client.on_message = mqtt_on_message

    # set last will in case of crash
    mqtt_client.will_set(constants.MQTT_AVAILABLE, "offline", qos=1, retain=True)

    mqtt_client.connect(args.mqtt)

    # subscribe to the built in topics
    watchTopics = [(constants.MQTT_SWITCH, 1), (constants.MQTT_COMMAND, 1), (constants.MQTT_NEW_TEXT, 1)]

    # get a list of all mqtt variables
    mqttVars = manager.get_variables_by_filter(constants.MQTT_CATEGORY)
    for v in mqttVars:
        watchTopics.append((v.get_topic(), v.get_qos()))

    # subscribe to the topics
    mqtt_client.subscribe(watchTopics)

    # starts the network loop in the background
    mqtt_client.loop_start()

    # let HA know we're online
    mqtt_client.publish(constants.MQTT_AVAILABLE, "online", retain=True)
    mqtt_publish_attributes()
else:
    logging.info("No MQTT server or username, skipping MQTT setup")

# go one day backward on first load (ie, force polling)
poll(timedelta(days=1))

while 1:
    # sleep for 1 min
    logging.debug('sleeping')
    time.sleep(60 - datetime.now().second)

    poll()
    find_active_queue()
