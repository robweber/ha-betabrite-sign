import datetime
import sys
import time
import lib.alphasign as alphasign
from lib.manager import MessageManager

# create global vars
betabrite = alphasign.interfaces.local.Serial(device='/dev/ttyUSB0')
labels = MessageManager('/home/pi/ha-betabrite-sign/data/layout.yaml')

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
    aVar = labels.getVariable('current_weather')

    haState = {"state":"53 and cloudy"}

    updateString('current_weather', aVar.getText().format(**haState))

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

print("Setting up sign")
setupSign()

time.sleep(10)

loadData()
