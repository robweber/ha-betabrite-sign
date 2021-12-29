import logging
import yaml
from . import alphasign
from .types.home_assistant import HomeAssistantVariable
from .types.time import DateVariable, TimeVariable

# dicts to transfrom yaml to alphasign variables
ALPHA_MODES = {"rotate":alphasign.modes.ROTATE, "hold":alphasign.modes.HOLD}
ALPHA_COLORS = {"green": alphasign.colors.GREEN, "orange": alphasign.colors.ORANGE, "rainbow1": alphasign.colors.RAINBOW_1,
                "rainbow2": alphasign.colors.RAINBOW_2, "red": alphasign.colors.RED, "yellow": alphasign.colors.YELLOW}
ALPHA_SPEEDS = {1: alphasign.speeds.SPEED_1, 2: alphasign.speeds.SPEED_2, 3: alphasign.speeds.SPEED_3,
                4: alphasign.speeds.SPEED_4, 5: alphasign.speeds.SPEED_5}


# manages loading of messages and variables from yaml file to create alphasign objects
class MessageManager:
    MESSAGE_STRING = "MESSAGESTRING"
    MESSAGE_TEXT = "MESSAGE"

    config = None  # yaml file
    stringObjs = {}  # alphasign string object Ids
    textObjs = {}  # alphasign text object ids
    varObjs = {}  # variables, extending VariableType

    def __init__(self, configFile):
        with open(configFile, 'r') as file:
            self.config = yaml.safe_load(file)

        self.__loadVariables()

    def __loadVariables(self):
        # load variables and store for later use
        for v in self.config['variables'].keys():
            aVar = self.config['variables'][v]

            if(aVar['type'] == 'date'):
                self.varObjs[v] = DateVariable(v, aVar)
            if(aVar['type'] == 'home_assistant'):
                self.varObjs[v] = HomeAssistantVariable(v, aVar)
            elif(aVar['type'] == 'time'):
                self.varObjs[v] = TimeVariable(v, aVar)

    def __allocateString(self, name):
        # strings use numbers for allocation
        nextInt = str(len(self.stringObjs) + 1)
        self.stringObjs[name] = nextInt

        return nextInt

    def __allocateText(self, name):
        # text objects use letters, convert from ASCII int value
        nextLetter = chr(len(self.textObjs) + 65)
        self.textObjs[name] = nextLetter

        return nextLetter

    def __generateTextParams(self, m):
        # color is required
        result = ALPHA_COLORS[m['color']]

        if('speed' in m):
            result = f"{result}{ALPHA_SPEEDS[m['speed']]}"

        return result

    def __getString(self, name):
        return self.stringObjs[name]

    def __getText(self, name):
        return self.textObjs[name]

    # initializes alphasign objects to load into sign memory
    def startup(self, betabrite):
        runList = []
        allocateStrings = []
        allocateText = []

        # load messages from "messages" key in yaml file
        for i in range(0, len(self.config['messages'])):
            # get the message
            aMessage = self.config['messages'][i]

            stringText = None
            # if "text" exists create a string object from static text
            if('text' in aMessage):
                stringObj = alphasign.String(data=aMessage['text'], label=self.__allocateString(f"{self.MESSAGE_STRING}_{i}"), size=125)
                allocateStrings.append(stringObj)
                stringText = stringObj.call()
            else:
                # message is data loaded from variables
                messageVars = aMessage['data']
                if(not isinstance(aMessage['data'], list)):
                    messageVars = [aMessage['data']]

                stringText = ""
                for v in messageVars:
                    # load each variable and extract it's startup text
                    aVar = self.varObjs[v]
                    logging.info("Loading variable %s:%s for message" % (aVar.getName(), aVar.getType()))
                    if(aVar.getType() == 'time'):
                        stringObj = aVar.getStartup()
                        betabrite.write(stringObj)
                    else:
                        stringObj = alphasign.String(data=aVar.getStartup(), label=self.__allocateString(aVar.getName()), size=125)
                        allocateStrings.append(stringObj)

                    stringText = f"{stringText} {stringObj.call()}"

            # create text object, setting the string text
            textParams = self.__generateTextParams(aMessage)
            alphaObj = alphasign.Text("%s%s" % (textParams, stringText), mode=ALPHA_MODES[aMessage['mode']], label=self.__allocateText(f"{self.MESSAGE_TEXT}_{i}"))

            allocateText.append(alphaObj)

            runList.append(alphaObj)

        # return objects that should be loaded into sign memory
        return {"run": runList, "allocate": allocateText + allocateStrings}

    def updateString(self, name, message):
        # create the string object
        return alphasign.String(data=message, label=self.__getString(name), size=125)

    def getVariable(self, name):
        return self.varObjs[name]

    def getVariables(self, category):
        # get variables that are part of a particular category
        return list(filter(lambda v: v.getCategory() == category, self.varObjs.values()))
