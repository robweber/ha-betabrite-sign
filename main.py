import configargparse
import json
import logging
import signal
import sys
import threading
import time
import lib.alphasign as alphasign
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as mqtt_subscribe
from jinja2 import Template
from datetime import datetime, timedelta
from termcolor import colored
from lib.manager import MessageManager
from lib.home_assistant import HomeAssistant, TemplateSyntaxError
from lib.constants import POLLING_CATEGORY, MQTT_CATEGORY, MQTT_STATUS, MQTT_ATTRIBUTES, MQTT_COMMAND, MQTT_AVAILABLE, SIGN_OFF

# create global vars
betabrite = None
manager = None
mqttClient = None
threadLock = threading.Lock()  # ensure exclusive access to betabrite serial port

def signal_handler(signum, frame):
    """function to handle when the is killed and exit gracefully"""
    logging.debug('Exiting Program')

    if(mqttClient is not None):
        # publish we're going offline
        mqttClient.publish(MQTT_AVAILABLE, "offline", retain=True)

        # disconnect
        mqttClient.loop_stop()
        mqttClient.disconnect()

    sys.exit(0)


def mqtt_connect(client, userdata, flags, rc):
    """run on successful mqtt connection"""
    logging.info("Connected to MQTT Server")


def mqtt_on_message(client, userdata, message):
    """triggered when message is received via mqtt"""
    logging.debug(colored(message.topic, 'red') + " " + str(message.payload))

    if(message.topic == MQTT_COMMAND):
        changeState(str(message.payload.decode('utf-8')))

        # publish new status and last updated attribute
        mqttClient.publish(MQTT_STATUS, message.payload, retain=True)
        mqttClient.publish(MQTT_ATTRIBUTES, json.dumps({"last_updated": str(datetime.now().astimezone().isoformat(timespec='seconds'))}), retain=True)
    else:
        # this is for a variable, load it
        aVar = manager.getVariableByFilter(MQTT_CATEGORY, lambda v: v.getTopic() == message.topic)

        if(aVar is not None):
            payload = str(message.payload.decode('utf-8'))

            if(aVar.parseJson()):
                payload = json.loads(payload)

            # render the template
            temp = Template(aVar.getText())
            newString = temp.render(value=payload)

            # update the data on the sign
            logging.debug(f"updated {aVar.getName()}:'{colored(newString, 'green')}'")
            updateString(aVar.getName(), newString)


def setupSign():
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
    pollingVars = manager.getVariablesByFilter(POLLING_CATEGORY, lambda v: v.shouldPoll(now, offset))

    # load the HA interface, if needed
    homeA = None
    if(args.ha_url and args.ha_token):
        homeA = HomeAssistant(args.ha_url, args.ha_token)

    for v in pollingVars:
        logging.info(f"Updating {v.getName()}")

        # update based on the type
        newString = None
        if(v.getType() == 'date'):
            newString = v.getText()
        elif(v.getType() == 'home_assistant'):
            if(homeA is not None):
                try:
                    # render the template in home assistant
                    newString = homeA.renderTemplate(v.getText()).strip()
                except TemplateSyntaxError as te:
                    logging.error(te)
            else:
                logging.error("Home Assistant interface is not loaded, specify HA url and token to load")

        if(newString is not None):
            logging.debug(f"updated {v.getName()}:'{colored(newString, 'green')}'")
            updateString(v.getName(), newString)


def changeState(newState):
    """changes the state of the sign on or off
    this is called when triggered via the MQTT_COMMAND topic

    :param newState: the new state of the sign (ON/OFF)
    """
    threadLock.acquire()
    betabrite.connect()

    # create the sign object and update the sign
    if(newState == 'OFF'):
        offMessage = manager.updateText(SIGN_OFF, ' ', True)
    else:
        offMessage = manager.updateText(SIGN_OFF, '', True)

    betabrite.write(offMessage)
    betabrite.disconnect()
    threadLock.release()

def updateString(name, msg):
    """Update a string object on the sign

    :param name: the name of the string to update, as defined in the yaml config
    :param msg: the message to send to the sign
    """
    # replace some chars
    msg = msg.replace('.', '')
    msg = msg.replace('_', ' ')

    strObj = manager.updateString(name, msg)
    threadLock.acquire()
    betabrite.connect()

    betabrite.write(strObj)

    betabrite.disconnect()
    threadLock.release()


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

setupSign()

# sleep for a few seconds
time.sleep(10)

if(args.mqtt and args.mqtt_username):
    # get the last known status from MQTT
    statusMsg = mqtt_subscribe.simple(MQTT_STATUS, hostname=args.mqtt, auth={"username": args.mqtt_username, "password": args.mqtt_password})
    logging.info(f"Startup state is: {colored(str(statusMsg.payload.decode('utf-8')), 'yellow')}")
    changeState(str(statusMsg.payload.decode('utf-8')))

    # setup the MQTT connection
    mqttClient = mqtt.Client()
    mqttClient.username_pw_set(args.mqtt_username, args.mqtt_password)

    # set the callback methods
    mqttClient.on_connect = mqtt_connect
    mqttClient.on_message = mqtt_on_message

    # set last will in case of crash
    mqttClient.will_set(MQTT_AVAILABLE, "offline", qos=1, retain=True)

    mqttClient.connect(args.mqtt)

    # subscribe to the built in topics
    watchTopics = [(MQTT_COMMAND, 1)]

    # get a list of all mqtt variables
    mqttVars = manager.getVariablesByFilter(MQTT_CATEGORY)
    for v in mqttVars:
        watchTopics.append((v.getTopic(), v.getQos()))

    # subscribe to the topics
    mqttClient.subscribe(watchTopics)

    # starts the network loop in the background
    mqttClient.loop_start()

    # let HA know we're online
    mqttClient.publish(MQTT_AVAILABLE, "online", retain=True)
else:
    logging.info("No MQTT server or username, skipping MQTT setup")

# go one day backward on first load (ie, force polling)
poll(timedelta(days=1))

while 1:
    # sleep for 1 min
    logging.debug('sleeping')
    time.sleep(60 - datetime.now().second)

    poll()
