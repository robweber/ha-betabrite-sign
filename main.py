import configargparse
import datetime
import sys
import time
import lib.alphasign as alphasign
from jinja2 import Template
from lib.manager import MessageManager
from lib.home_assistant import HomeAssistant
from lib.variable_type import POLLING_CATEGORY

# create global vars
betabrite = None
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
        entities = {}
        if(v.getType() == 'home_assistant'):
            if(homeA is not None):
                # load the status of any entities needed
                for e in v.getEntities():
                    entities[e] = homeA.getState(e)

                print("found %d entities" % len(entities))
                # update the string
                template = Template(v.getText())
                updateString(v.getName(), template.render(vars=entities).strip())
            else:
                print("Home Assistant interface is not loaded, specify HA url and token to load")

def updateString(name, msg):
    #replace some chars
    msg = msg.replace('.','')
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
parser.add_argument('-d', '--device', default="/dev/ttyUSB0",
                    help="Path to device where Alphasign is connected, default is %(default)s, can also use 'cli' to output to screen only")
parser.add_argument('-u', '--url', required=False,
                    help="Home Assistant full base url")
parser.add_argument('-t', '--token', required=False,
                    help="Home Assistant Access Token")
parser.add_argument('-D', '--debug', action='store_true',
                    help='Enables logging debug mode')

args = parser.parse_args()

print("Setting up sign")

if(args.device == 'cli'):
    print('Outputting sign info to CLI')
    betabrite = alphasign.interfaces.local.DebugInterface()
else:
    betabrite = alphasign.interface.local.Serial(device=args.device)

print("Loading layout: " + args.layout)
labels = MessageManager(args.layout)

# load the HA interface, if needed
if(args.url and args.token):
    homeA = HomeAssistant(args.url, args.token)

setupSign()

time.sleep(10)

loadData()
