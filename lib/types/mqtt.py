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

import re
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
    __depends = None

    def __init__(self, name, config):
        super().__init__('mqtt', name, config, {"qos": 0, 'update_template': "True", "template": "{{ value }}"})

        # get variables this var depends on
        self.__depends = []
        matches = re.findall("get_payload\('\w+'\)", self.get_text())  # noqa: W605
        for m in matches:
            depend = m[13:-2]  # strip the function from the var name
            if(depend not in self.__depends):
                self.__depends.append(depend)

    def get_dependencies(self):
        return self.__depends

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
