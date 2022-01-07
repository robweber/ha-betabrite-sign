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

from jinja2 import Template
from .. import constants
from .. variable_type import VariableType


class MQTTVariable(VariableType):
    """The MQTT variable watches a specific MQTT topic for updates

    Special configuration options are:
      * topic: the MQTT topic to monitor for updates
      * template: what to render on the sign
      * qos: the MQTT quality of service (0-2) to use
    """

    def __init__(self, name, config):
        super().__init__('mqtt', name, config, {"qos": 0, 'update_template': "True"})

    def get_topic(self):
        return self.config['topic']

    def get_qos(self):
        return self.config['qos']

    def should_update(self, current_payload, previous_payload):
        """determine if the text of this variable should be updated based on a templated
        conditional in the yaml configuration. By default this will always return True unless
        defined otherwise.

        :param current_payload: the current payload from the MQTT topic
        :param previous_payload: the previous payload

        :returns: boolean value, True/False
        """
        # create a template from the update conditional
        template = Template(self.config['update_template'])

        # evaluate it and return the result as a boolean
        result = template.render(value=current_payload, previous=previous_payload).strip()
        return result.lower() == "true"

    def get_text(self):
        return self.config['template']

    def get_category(self):
        return constants.MQTT_CATEGORY
