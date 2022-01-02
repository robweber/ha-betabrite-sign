import logging
import yaml
from . import alphasign
from . import constants
from .types.home_assistant import HomeAssistantVariable
from .types.static import StaticVariable
from .types.time import DateVariable, TimeVariable


class MessageManager:
    """Manages the creation of messages and variables from
    the yaml config file to create alphasign objects
    """
    MESSAGE_TEXT = "MESSAGE"

    config = None  # yaml file
    stringObjs = {}  # alphasign string object Ids
    textObjs = {}  # alphasign text object ids
    varObjs = {}  # variables, extending VariableType

    def __init__(self, configFile):
        """
        :param configFile: path to the yaml configuration file
        """
        with open(configFile, 'r') as file:
            self.config = yaml.safe_load(file)

        # load all variable objects right away
        self.__loadVariables()

    def __loadVariables(self):
        """create VariableType objects from the variables
        key in the yaml file
        """
        for v in self.config['variables'].keys():
            aVar = self.config['variables'][v]

            if(aVar['type'] == 'date'):
                self.varObjs[v] = DateVariable(v, aVar)
            elif(aVar['type'] == 'home_assistant'):
                self.varObjs[v] = HomeAssistantVariable(v, aVar)
            elif(aVar['type'] == 'static'):
                self.varObjs[v] = StaticVariable(v, aVar)
            elif(aVar['type'] == 'time'):
                self.varObjs[v] = TimeVariable(v, aVar)

    def __allocateString(self, name):
        """create a string label to allocate on the sign

        :returns: the next string allocation number
        """
        # strings use numbers for allocation
        nextInt = str(len(self.stringObjs) + 1)
        self.stringObjs[name] = nextInt

        return nextInt

    def __allocateText(self, name):
        """create a text label to allocate on the sign

        :returns: the next allocation letter
        """
        # text objects use letters, convert from ASCII int value
        nextLetter = chr(len(self.textObjs) + 65)
        self.textObjs[name] = nextLetter

        return nextLetter

    def __generateTextParams(self, m):
        """takes the configuration options and turns
        them into alphasign parameters to send to the display

        :returns: string object containing the valid alphasign codes
        """
        result = ""

        if('color' in m):
            result = f"{constants.ALPHA_COLORS[m['color']]}"

        if('font' in m):
            result = f"{result}{constants.ALPHA_FONTS[m['font']]}"

        if('speed' in m):
            result = f"{result}{constants.ALPHA_SPEEDS[m['speed']]}"

        return result

    def __getString(self, name):
        """lookup a previously allocated string

        :returns: the allocation number identified by this string ID
        """
        if(name not in self.stringObjs.keys()):
            raise UndefinedVariableError(name)

        return self.stringObjs[name]

    def __getText(self, name):
        """lookup a previously allocated text object

        :returns: the allocation letter identified by this text ID
        """
        return self.textObjs[name]

    def startup(self, betabrite):
        """initializes alphasign objects to load into sign memory
        :param betabrite: a valid alphasign BaseInterface

        :returns: a dict containing objects to allocate and write to the sign
        """
        runList = []
        allocateStrings = {}  # name: stringObj value
        allocateText = []  # textObjs

        # load messages from "messages" key in yaml file
        for i in range(0, len(self.config['messages'])):
            # get the message
            aMessage = self.config['messages'][i]

            # load message data from variables
            messageVars = aMessage['data']
            if(not isinstance(aMessage['data'], list)):
                messageVars = [aMessage['data']]

            stringText = ""
            cliText = ""
            for v in messageVars:
                # load each variable and extract it's startup text
                if(v in self.varObjs.keys()):
                    aVar = self.varObjs[v]

                    stringObj = None
                    if(v in allocateStrings.keys()):
                        # use pre-allocated string object if already loaded once
                        logging.info(f"{aVar.getName()} alreadying loaded, adding to message")
                        stringObj = allocateStrings[v]
                        cliText = f"{cliText} {aVar.render(v)}"
                    else:
                        logging.info(f"Loading variable {aVar.getName()}:{aVar.getType()} for message")
                        if(aVar.getType() == 'time'):
                            stringObj = aVar.getStartup()
                            betabrite.write(stringObj)
                            cliText = f"{cliText} {aVar.render()}"
                        else:
                            stringObj = alphasign.String(data=aVar.getStartup(),
                                                         label=self.__allocateString(aVar.getName()), size=125)
                            allocateStrings[v] = stringObj
                            cliText = f"{cliText} {aVar.render(aVar.getStartup())}"

                    stringText = f"{stringText} {aVar.getDisplayParams()}{stringObj.call()}"
                else:
                    # kill the process here, can't recover from this
                    raise UndefinedVariableError(v)

            # create text object, setting the string text
            logging.debug(f"{cliText} - MODE: {aMessage['mode']}")
            messageParams = self.__generateTextParams(aMessage)
            alphaObj = alphasign.Text("%s%s" % (messageParams, stringText), mode=constants.ALPHA_MODES[aMessage['mode']],
                                      label=self.__allocateText(f"{self.MESSAGE_TEXT}_{i}"))

            allocateText.append(alphaObj)

            runList.append(alphaObj)

        # return objects that should be loaded into sign memory
        return {"run": runList, "allocate": allocateText + list(allocateStrings.values())}

    def updateString(self, name, message):
        """Updates a string object on the sign with a new message
        :param name: the name, as defined in yaml, of the variable to update
        :message message: the new message

        :returns: alphasign String object that can be written to the sign
        """
        # create the string object
        return alphasign.String(data=message, label=self.__getString(name), size=125)

    def getVariable(self, name):
        """finds the VariableType object associated with the given name
        :param name: the name, as defined in yaml, of the variable to lookup

        :returns: the VariableType object
        """
        return self.varObjs[name]

    def getVariables(self, category):
        """find all variables of a given category
        :param category: the category (polling, etc) to filter

        :returns: a list of all variables that match the given VariableType category
        """
        # get variables that are part of a particular category
        return list(filter(lambda v: v.getCategory() == category, self.varObjs.values()))


class UndefinedVariableError(Exception):
    """This error is thrown when the key passed to lookup a variable
    cannot be found. It most likely does not exist in the config file
    """

    def __init__(self, varName):
        super().__init__(f"The variable '{varName}' does not exist or is not allocated")
