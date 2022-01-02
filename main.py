import configargparse
import logging
import signal
import sys
import time
import lib.alphasign as alphasign
import paho.mqtt.client as mqtt
from jinja2 import Template
from datetime import datetime, timedelta
from lib.manager import MessageManager
from lib.home_assistant import HomeAssistant, TemplateSyntaxError
from lib.constants import POLLING_CATEGORY, MQTT_STATUS, MQTT_COMMAND

# create global vars
betabrite = None
homeA = None
manager = None
mqttClient = None

# function to handle when the is killed and exit gracefully
def signal_handler(signum, frame):
    logging.debug('Exiting Program')
    mqttClient.loop_stop()
    mqttClient.disconnect()
    sys.exit(0)

def mqtt_connect(client, userdata, flags, rc):
    logging.info("Connected to MQTT Server")

def mqtt_on_message(client, userdata, message):
    logging.debug(message.topic + " " + str(message.payload))

    if(message.topic == MQTT_COMMAND):
        mqttClient.publish(MQTT_STATUS, message.payload, retain=True)

def setupSign():
    """Setup the sign by allocated memory for variables and messages
    """
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
    # get all polling type variables
    pollingVars = manager.getVariables(POLLING_CATEGORY)

    now = datetime.now()
    for v in pollingVars:
        # check if the variable should be updated
        if(v.shouldPoll(now, offset)):
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
                logging.debug(f"updated {v.getName()}:{v.render(newString)}")
                updateString(v.getName(), newString)


def updateString(name, msg):
    """Update a string object on the sign

    :param name: the name of the string to update, as defined in the yaml config
    :param msg: the message to send to the sign
    """
    # replace some chars
    msg = msg.replace('.', '')
    msg = msg.replace('_', ' ')

    strObj = manager.updateString(name, msg)

    betabrite.connect()

    betabrite.write(strObj)

    betabrite.disconnect()


# parse the arguments
parser = configargparse.ArgumentParser(description='Home Assistant Betabrite Sign')
parser.add_argument('-c', '--config', is_config_file=True,
                    help='Path to custom config file')
parser.add_argument('-l', '--layout', default="data/layout.yaml",
                    help="Path to yaml file containing sign text layout, default is %(default)s")
parser.add_argument('-d', '--device', default="/dev/ttyUSB0",
                    help="Path to device where Alphasign is connected, default is %(default)s, can also use 'cli' to output to screen only")
parser.add_argument('-u', '--url', required=False,
                    help="Home Assistant full base url")
parser.add_argument('-t', '--token', required=False,
                    help="Home Assistant Access Token")
parser.add_argument('-m', '--mqtt', required=False,
                    help="MQTT Server IP")
parser.add_argument('-U', '--mqtt_username', required=False,
                    help="MQTT Server username")
parser.add_argument('-P', '--mqtt_password', required=False,
                    help="MQTT Server password")
parser.add_argument('-D', '--debug', action='store_true',
                    help='Enables logging debug mode')

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

# load the HA interface, if needed
if(args.url and args.token):
    homeA = HomeAssistant(args.url, args.token)

setupSign()

# sleep for a few seconds
time.sleep(10)

# setup the MQTT connection
mqttClient = mqtt.Client()

mqttClient.username_pw_set(args.mqtt_username, args.mqtt_password)
mqttClient.on_connect = mqtt_connect
mqttClient.on_message = mqtt_on_message

mqttClient.connect(args.mqtt)

mqttClient.subscribe(MQTT_STATUS)
mqttClient.subscribe(MQTT_COMMAND)

mqttClient.loop_start()

# go one day backward on first load (ie, force polling)
poll(timedelta(days=1))

while 1:
    # sleep for 1 min
    logging.debug('sleeping')
    time.sleep(60 - datetime.now().second)

    poll()
