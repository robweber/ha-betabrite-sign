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

import logging
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

        # get variables this var depends on based on 'get_payload' or 'is_payload' type functions
        # uses matching per description https://docs.python.org/3/library/re.html#re.findall
        self.__depends = []
        matches = re.findall("(is_payload(_attr)?\('(\w+)',)|(get_payload(_attr)?\('(\w+)'(,)?)", self.get_text())  # noqa: W605
        for m in matches:
            # will be in group 2 or 5
            depend = m[2] if m[2] != '' else m[5]
            if(depend not in self.__depends):
                self.__depends.append(depend)

        if(len(self.__depends) > 0):
            logging.debug(f"{name} dependencies: {self.__depends}")

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
        return [constants.MQTT_CATEGORY]
