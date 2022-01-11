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

import jinja2
from .. import constants
from .. variable_type import VariableType


class MQTTVariable(VariableType):
    """The MQTT variable watches a specific MQTT topic for updates

    Special configuration options are:
      * topic: the MQTT topic to monitor for updates
      * template: what to render on the sign
      * qos: the MQTT quality of service (0-2) to use
      * update_template: eval True/False if this template should be updated
    """

    def __init__(self, name, config):
        super().__init__('mqtt', name, config, {"qos": 0, 'update_template': "True", "template": "{{ value }}"})

    def get_topic(self):
        return self.config['topic']

    def get_qos(self):
        return self.config['qos']

    def update_template(self):
        return self.config['update_template']

    def get_text(self):
        return self.config['template']

    def get_category(self):
        return constants.MQTT_CATEGORY


class MQTTPayloadManager:
    """Manages information about MQTT topic payloads and evaluates
    templates via Jinja from MQTT variables
    """
    __jinja_env = None
    __payloads = {}

    def __init__(self, vars):
        """
        :params vars: list of MQTT variable objects
        """
        # initalize each variable
        var_names = [v.get_name() for v in vars]
        self.__payloads = dict.fromkeys(var_names, "")

        # setup jinja environment
        self.__jinja_env = jinja2.Environment()
        self.__jinja_env.globals['get_payload'] = self.get_payload

    def set_payload(self, var, payload):
        """set the given MQTT payload for this variable name
        :param var: the MQTT variable name as a string
        :param payload: the topic payload
        """
        self.__payloads[var] = payload

    def get_payload(self, var):
        """return the payload, if any, for this variable

        :param var: the MQTT variable name

        :returns: the payload
        """
        return self.__payloads[var]

    def has_value(self, var):
        """does this variable have a valid payload
        :param var: the MQTT variable name

        :returns: True/False
        """
        return self.__payloads[var] != ""

    def should_update(self, var, payload):
        """evaluate the update_template conditional of this variable
        in the yaml configuration. By default this will always return True unless
        defined otherwise.

        :param var: the MQTT variable object
        :param payload: the new payload from the topic

        :returns: boolean value, True/False
        """
        template = self.__jinja_env.from_string(var.update_template())

        # evaluate it and return the result as a boolean
        result = template.render(value=payload, previous=self.get_payload(var.get_name())).strip()
        return result.lower() == "true"

    def render_template(self, var, payload):
        """render the template for this variable
        the new payload is passed in as the "value" variable
        and the old payload as the "previous" variable

        :param var: the MQTT variable object
        :param payload: the new payload from the topic

        :returns: the result of the rendered template
        """
        template = self.__jinja_env.from_string(var.get_text())

        return template.render(value=payload, previous=self.get_payload(var.get_name())).strip()
