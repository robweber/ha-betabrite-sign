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

import alphasign
import jinja2
import logging
import sys
import yaml
from cerberus import Validator
from termcolor import colored
from . import constants
from . import jinja_custom
from .types.home_assistant import HomeAssistantVariable
from .types.mqtt import MQTTVariable
from .types.rest import RestVariable
from .types.text import DynamicVariable, StaticVariable
from .types.time import DateVariable, TimeVariable


class MessageManager:
    """Manages the creation of messages and variables from
    the yaml config file to create alphasign objects
    """
    MESSAGE_TEXT = "MESSAGE"

    config = None  # yaml file
    stringObjs = {}  # alphasign string object Ids
    textObjs = {}  # alphasign text object ids
    runList = {}
    varObjs = {}  # variables, extending VariableType

    def __init__(self, configFile):
        """:param configFile: path to the yaml configuration file"""

        # load the schema and config file
        with open('data/schema.yaml', 'r') as file:
            schema = yaml.safe_load(file)

        with open(configFile, 'r') as file:
            self.config = yaml.safe_load(file)

        # validate the config, kill the program if invalid
        v = Validator(schema)
        if(not v.validate(self.config, schema)):
            logging.error(f"Error in layout file: {configFile}")
            logging.error(str(v.errors))
            sys.exit(2)

        # load all variable objects right away
        self.__load_variables()

        # add a special variable for the MQTT Text Entity
        self.varObjs[constants.TEXT_ENTITY_VARIABLE] = MQTTVariable(constants.TEXT_ENTITY_VARIABLE, {"topic": constants.MQTT_CURRENT_TEXT})

    def __load_variables(self):
        """create VariableType objects from the variables
        key in the yaml file
        """
        for v in self.config['variables'].keys():
            aVar = self.config['variables'][v]

            if(aVar['type'] == 'date'):
                self.varObjs[v] = DateVariable(v, aVar)
            elif(aVar['type'] == 'mqtt'):
                self.varObjs[v] = MQTTVariable(v, aVar)
            elif(aVar['type'] == 'home_assistant'):
                self.varObjs[v] = HomeAssistantVariable(v, aVar)
            elif(aVar['type'] == 'static'):
                self.varObjs[v] = StaticVariable(v, aVar)
            elif(aVar['type'] == 'time'):
                self.varObjs[v] = TimeVariable(v, aVar)
            elif(aVar['type'] == 'rest'):
                self.varObjs[v] = RestVariable(v, aVar)
            elif(aVar['type'] == 'dynamic'):
                self.varObjs[v] = DynamicVariable(v, aVar)

    def __get_char(self, start, offset):
        """helper method to return a single character based on the
        ASCII start point and an offset to add to it
        for example __get_char(65, 2) would be the character 'C' which is ASCII 67

        :param start: the ascii start number
        :param offset: the offset to add to the start

        :returns: the character defined start + offset
        """

        return chr(start + offset)

    def __allocate_string(self, name):
        """create a string label to allocate on the sign

        :returns: the next string allocation number
        """
        # strings use lowercase letters, convert from ASCII int value
        nextLetter = self.__get_char(97, len(self.stringObjs))

        self.stringObjs[name] = nextLetter

        return nextLetter

    def __allocate_text(self, name):
        """create a text label to allocate on the sign

        :returns: the next allocation letter
        """
        # text objects use capital letters, convert from ASCII int value
        nextLetter = self.__get_char(65, len(self.textObjs))
        self.textObjs[name] = nextLetter

        return nextLetter

    def __generate_text_params(self, m):
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

    def __get_string(self, name):
        """lookup a previously allocated string

        :returns: the allocation number identified by this string ID
        """
        result = None
        if(name in self.stringObjs.keys()):
            result = self.stringObjs[name]

        return result

    def __get_text(self, name):
        """lookup a previously allocated text object

        :returns: the allocation letter identified by this text ID
        """
        return self.textObjs[name]

    def startup(self, betabrite):
        """initializes alphasign objects to load into sign memory
        :param betabrite: a valid alphasign BaseInterface

        :returns: a dict containing objects to allocate and write to the sign
        """
        allocateStrings = {}  # name: stringObj value
        allocateText = []  # textObjs

        # create a special message for when the sign is off
        offMessage = alphasign.Text(data="", label=self.__allocate_text(constants.SIGN_OFF), mode=constants.ALPHA_MODES['hold'])
        allocateText.append(offMessage)

        # load all queues from the display section of the yaml file
        for q in self.config['display']:
            self.runList[q] = []

            # go through all messages in this queue
            for i in range(0, len(self.config['display'][q]['queue'])):
                aMessage = self.config['display'][q]['queue'][i]

                # create message from variables
                messageVars = aMessage['message']
                if(not isinstance(aMessage['message'], list)):
                    messageVars = [aMessage['message']]

                stringText = []
                cliText = []
                for v in messageVars:
                    # load each variable and extract it's startup text
                    if(v in self.varObjs.keys()):
                        aVar = self.varObjs[v]

                        stringObj = None
                        if(v in allocateStrings.keys()):
                            # use pre-allocated string object if already loaded once
                            logging.info(f"{aVar.get_name()} already loaded, adding to message")
                            stringObj = allocateStrings[v]
                            cliText.append(colored(v, 'green'))
                        else:
                            logging.info(f"Loading variable {aVar.get_name()}:{aVar.get_type()} for message")
                            if(aVar.get_type() == 'time'):
                                stringObj = aVar.get_text()
                                betabrite.write(stringObj.set_format(aVar.get_time_format()))  # write the time format
                                betabrite.write(stringObj.set())
                                betabrite.write(stringObj)
                                cliText.append(colored(aVar.get_startup(), 'green'))
                            else:
                                stringObj = alphasign.String(data=aVar.get_startup(),
                                                             label=self.__allocate_string(aVar.get_name()), size=125)
                                allocateStrings[v] = stringObj
                                cliText.append(colored(aVar.get_startup(), 'green'))

                        stringText.append(f"{aVar.get_display_params()}{stringObj.call()}")
                    else:
                        # kill the process here, can't recover from this
                        raise UndefinedVariableError(v)

                # create text object, setting the string text
                logging.debug(f"'{' '.join(cliText)}' - MODE: {aMessage['mode']}")
                messageParams = self.__generate_text_params(aMessage)
                alphaObj = alphasign.Text("%s%s" % (messageParams, ' '.join(stringText)), mode=constants.ALPHA_MODES[aMessage['mode']],
                                          label=self.__allocate_text(f"{self.MESSAGE_TEXT}_{q}_{i}"))

                allocateText.append(alphaObj)

                self.runList[q].append(alphaObj)

        # return objects that should be loaded into sign memory
        return {"run": self.runList['main'], "allocate": allocateText + list(allocateStrings.values())}

    def update_string(self, name, message):
        """Updates a string object on the sign with a new message

        :param name: the name, as defined in yaml, of the variable to update
        :message message: the new message

        :returns: alphasign String object that can be written to the sign
        """
        result = None
        id = self.__get_string(name)

        if(id is not None):
            # create the string object
            result = alphasign.String(data=message, label=id, size=125)

        return result

    def update_text(self, name, message, priority=False):
        """Updates a Text object on the sign with a new message
        using update_string is preferable in most cases but this allows the swapping out of
        messages with the priority flag

        :param name: the name of the text object to update
        :param message: the new message
        :param priority: if the message should take the place of currently shown messages. Defaults to False.
        if set to True with a blank message it will erase the priority flag

        :returns: alphasign Text object that can be written to the sign
        """
        return alphasign.Text(data=message, label=self.__get_text(name), priority=priority)

    def find_active_queue(self, evaluator):
        """returns the currently active message queue from evaluating the active_template
        associated with each queue. If none are found "main" is returned

        :param evaluator: the PayloadManager class to use in evaluating the templates

        :returns: the active message queue name
        """
        result = "main"

        for q in self.config['display']:
            if(q != "main" and 'active_template' in self.config['display'][q]):
                template = self.config['display'][q]['active_template']

                if(evaluator.render_template(template).lower() == "true"):
                    result = q
                    break

        return result

    def get_queue(self, name):
        """get the message queue given by the name, if it exits, otherwise return the main queue

        :param name: the name of the queue to find

        :returns: the message queue as a list
        """
        result = None

        if(name in self.runList.keys()):
            result = self.runList[name]
        else:
            result = self.runList["main"]

        return result

    def get_variable_by_name(self, name):
        """finds the VariableType object associated with the given name
        :param name: the name, as defined in yaml, of the variable to lookup

        :returns: the VariableType object
        """
        return self.varObjs[name]

    def get_variable_by_filter(self, category, func=lambda v: True):
        """exact same functionality as get_variables_by_filter below
        however this is guarenteed to return a single result instead of a list

        :return: the VariableType object, could be None if not found or more than one result
        """
        result = None

        foundVars = self.get_variables_by_filter(category, func)

        # only return an object if exactly one is found
        if(len(foundVars) == 1):
            result = foundVars[0]

        return result

    def get_variables_by_filter(self, category, func=lambda v: True):
        """find all variables of a given category

        :param category: the category, or array of categories, (polling, etc) to filter
        :param func: an optional function to further filter the list by,
        this should be a lambda expression that takes a single argument

        :returns: a list of all variables that match the given VariableType categories
        """
        # get variables that are part of a particular category or group of categories
        if(not isinstance(category, list)):
            category = [category]

        return list(filter(lambda v: len(set(v.get_categories()).intersection(category)) > 0 and func(v), self.varObjs.values()))


class PayloadManager:
    """Manages information about variable state payloads and evaluates
    templates via Jinja
    """
    __jinja_env = None
    __rendered_templates = None
    __payloads = None
    __depends = None

    def __init__(self, vars):
        """
        :params vars: list of Jinja variable objects
        """
        # initalize each variable
        var_names = [v.get_name() for v in vars]
        self.__payloads = dict.fromkeys(var_names, "")
        self.__rendered_templates = dict.fromkeys(var_names, "")

        # setup jinja environment - functions and filters
        self.__jinja_env = jinja2.Environment()
        self.__jinja_env.globals['get_payload'] = self.get_payload
        self.__jinja_env.globals['get_payload_attr'] = self.get_payload_attribute
        self.__jinja_env.globals['is_payload'] = self.is_payload
        self.__jinja_env.globals['is_payload_attr'] = self.is_payload_attribute
        self.__jinja_env.globals['now'] = jinja_custom.get_date
        self.__jinja_env.globals['timedelta'] = jinja_custom.get_timedelta
        self.__jinja_env.globals['strptime'] = jinja_custom.create_time
        self.__jinja_env.globals['is_time'] = jinja_custom.is_time

        self.__jinja_env.filters['shorten_urls'] = jinja_custom.shorten_urls
        self.__jinja_env.filters['color'] = jinja_custom.set_color

        # get any variable dependencies
        self.__depends = {}
        for v in vars:
            for d in v.get_dependencies():
                if(d in self.__depends.keys()):
                    self.__depends[d].append(v.get_name())
                else:
                    self.__depends[d] = [v.get_name()]

    def set_payload(self, var, payload):
        """set the given payload for this variable name
        :param var: the variable name as a string
        :param payload: the topic payload
        """
        self.__payloads[var] = payload

    def get_payload(self, var):
        """return the payload, if any, for this variable

        :param var: the variable name

        :returns: the payload or a blank string if it doesn't exist
        """
        result = ""
        if(var in self.__payloads.keys()):
            result = self.__payloads[var]

        return result

    def get_payload_attribute(self, var, attr):
        """return the attribute of a given variable payload
        useful when you know the payload is a JSON dict

        :param var: the variable name
        :param attr: the attribute to lookup on this variable

        :returns: the value of the attribute given, could be None if attribute doesn't exist
        """
        result = None
        # first get the payload and test if the attribute exists
        payload = self.get_payload(var)

        if(type(payload) is dict and attr in payload):
            result = payload[attr]

        return result

    def is_payload(self, var, expected_value):
        """compares the given variable's payload against the expected value to return
        either True or False, the same as doing get_payload() == "expected_value"

        :param var: the variable name
        :param expected_value: the comparison value

        :returns: True if variable payload equals the expected_value, false if otherwise
        """
        payload = self.get_payload(var)

        return payload == expected_value

    def is_payload_attribute(self, var, attr, expected_value):
        """combination of is_payload and get_payload_attr, will find the payload attribute
        and compare it to the expected value. If the attribute does not exist this will return
        False

        :param var: the variable name
        :param attr: the attribute to look up on this variable
        :param expected_value: the comparison value

        :returns: True if the variable attribute equals the expected_value, False if attribute doesn't exist or value isn't equal
        """
        result = False
        payload = self.get_payload_attribute(var, attr)

        if(payload is not None):
            result = payload == expected_value

        return result

    def get_dependencies(self, var):
        """get any variables that uses the given variable in a template via get_payload

        :param var: the variable name

        :returns: a list of dependency variable names, or a blank list if none
        """
        result = []
        if(var in self.__depends.keys()):
            result = self.__depends[var]

        return result

    def has_value(self, var):
        """does this variable have a valid payload
        :param var: the variable name

        :returns: True/False
        """
        return self.__payloads[var] != ""

    def should_update(self, var):
        """evaluate the update_template conditional of this variable
        in the yaml configuration. By default this will always return True unless
        defined otherwise.

        :param var: the variable object

        :returns: boolean value, True/False
        """
        template = self.__jinja_env.from_string(var.update_template())

        # evaluate it and return the result as a boolean
        result = template.render(value=self.get_payload(var.get_name())).strip()
        return result.lower() == "true"

    def render_variable(self, var):
        """render the template for this variable
        the payload is passed in as the "value" variable

        :param var: the variable object

        :returns: the result of the rendered template, None if this result
        is the same as the previously rendered result (no change)
        """
        result = None  # assume no change

        template = self.__jinja_env.from_string(var.get_text())

        r = template.render(value=self.get_payload(var.get_name())).strip()

        if(r != self.__rendered_templates[var.get_name()]):
            # return result if different than previous
            result = r
            self.__rendered_templates[var.get_name()] = result

        return result

    def render_template(self, template_string):
        """generically renders a template string

        :param template: the jinja template string

        :returns: the result of the rendered template
        """

        template = self.__jinja_env.from_string(template_string)

        return template.render().strip()


class UndefinedVariableError(Exception):
    """This error is thrown when the key passed to lookup a variable
    cannot be found. It most likely does not exist in the config file
    """

    def __init__(self, varName):
        super().__init__(f"The variable '{varName}' does not exist or is not allocated")
