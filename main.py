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
from jinja2 import Template
from datetime import datetime, timedelta
from termcolor import colored
from lib.manager import MessageManager
from lib.home_assistant import HomeAssistant, TemplateSyntaxError
from lib import constants

# create global vars
betabrite = None
manager = None
mqtt_client = None
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


def mqtt_on_message(client, userdata, message):
    """triggered when message is received via mqtt"""
    logging.debug(colored(message.topic, 'red') + " " + str(message.payload))

    if(message.topic == constants.MQTT_COMMAND):
        change_state(str(message.payload.decode('utf-8')))

        # publish new status and last updated attribute
        mqtt_client.publish(constants.MQTT_STATUS, message.payload, retain=True)
        mqtt_client.publish(constants.MQTT_ATTRIBUTES, json.dumps({"last_updated": str(datetime.now().astimezone().isoformat(timespec='seconds'))}), retain=True)
    else:
        # this is for a variable, load it
        aVar = manager.get_variable_by_filter(constants.MQTT_CATEGORY, lambda v: v.get_topic() == message.topic)

        if(aVar is not None):
            payload = str(message.payload.decode('utf-8'))

            if(aVar.parse_json()):
                payload = json.loads(payload)

            # render the template
            temp = Template(aVar.get_text())
            newString = temp.render(value=payload)

            # update the data on the sign
            logging.debug(f"updated {aVar.get_name()}:'{colored(newString, 'green')}'")
            update_string(aVar.get_name(), newString)


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
        logging.info(f"Updating {v.get_name()}")

        # update based on the type
        newString = None
        if(v.get_type() == 'date'):
            newString = v.get_text()
        elif(v.get_type() == 'home_assistant'):
            if(homeA is not None):
                try:
                    # render the template in home assistant
                    newString = homeA.render_template(v.get_text()).strip()
                except TemplateSyntaxError as te:
                    logging.error(te)
            else:
                logging.error("Home Assistant interface is not loaded, specify HA url and token to load")

        if(newString is not None):
            logging.debug(f"updated {v.get_name()}:'{colored(newString, 'green')}'")
            update_string(v.get_name(), newString)


def change_state(newState):
    """changes the state of the sign on or off
    this is called when triggered via the MQTT_COMMAND topic

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


def update_string(name, msg):
    """Update a string object on the sign

    :param name: the name of the string to update, as defined in the yaml config
    :param msg: the message to send to the sign
    """
    # replace some chars
    msg = msg.replace('.', '')
    msg = msg.replace('_', ' ')

    strObj = manager.update_string(name, msg)
    thread_lock.acquire()
    betabrite.connect()

    betabrite.write(strObj)

    betabrite.disconnect()
    thread_lock.release()


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

logging.info("Setting up sign")

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

if(args.mqtt and args.mqtt_username):
    # get the last known status from MQTT
    statusMsg = mqtt_subscribe.simple(constants.MQTT_STATUS, hostname=args.mqtt, auth={"username": args.mqtt_username, "password": args.mqtt_password})
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
    watchTopics = [(constants.MQTT_COMMAND, 1)]

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
else:
    logging.info("No MQTT server or username, skipping MQTT setup")

# go one day backward on first load (ie, force polling)
poll(timedelta(days=1))

while 1:
    # sleep for 1 min
    logging.debug('sleeping')
    time.sleep(60 - datetime.now().second)

    poll()
