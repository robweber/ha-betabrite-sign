import configargparse
import datetime
import sys
import time
import lib.alphasign as alphasign
from lib.manager import MessageManager
from lib.home_assistant import HomeAssistant
from lib.variable_type import POLLING_CATEGORY

# create global vars
betabrite = alphasign.interfaces.local.Serial(device='/dev/ttyUSB0')
homeA = None
labels = None

def setupSign():
    runList = []
    allocateList = []

    betabrite.connect()
    betabrite.clear_memory()

    # wait for sign to clear memory
    time.sleep(2)

    messages = labels.startup(betabrite)

    print('allocating and sending run sequence')
    betabrite.allocate(tuple(messages['allocate']))
    #set the run sequence
    betabrite.set_run_sequence(tuple(messages['run']))

    print('writing objects list')
    for obj in messages['allocate']:
        betabrite.write(obj)

    betabrite.disconnect()

def loadData():
    # get all polling type variables
    pollingVars = labels.getVariables(POLLING_CATEGORY)

    for v in pollingVars:
        if(v.getType() == 'home_assistant'):
            # load the status of this entity
            state = homeA.getState(v.getEntity())

            # update the string
            updateString(v.getName(), state['state'])

def updateString(name, msg):
    #replace some chars
    msg = msg.replace('.','')
    msg = msg.replace(':','')
    msg = msg.replace('_',' ')

    print("%s: %s" % (name, msg))
    strObj = labels.updateString(name, msg)

    betabrite.connect()

    betabrite.write(strObj)

    betabrite.disconnect()

# parse the arguments
parser = configargparse.ArgumentParser(description='Home Assistant Betabrite Sign')
parser.add_argument('-c', '--config', is_config_file=True,
                    help='Path to custom config file')
parser.add_argument('-l', '--layout', default="data/layout.yaml",
                    help="Path to yaml file containing sign text layout, default is %(default)s")
parser.add_argument('-u', '--url', required=True,
                    help="Home Assistant full base url")
parser.add_argument('-t', '--token', required=True,
                    help="Home Assistant Access Token")

args = parser.parse_args()

print("Setting up sign")
print("Loading layout: " + args.layout)
labels = MessageManager(args.layout)
homeA = HomeAssistant(args.url, args.token)

setupSign()

time.sleep(10)

loadData()
