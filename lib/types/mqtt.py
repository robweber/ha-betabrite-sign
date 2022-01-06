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

from .. import constants
from .. variable_type import VariableType


class MQTTVariable(VariableType):
    """The MQTT variable watches a specific MQTT topic for updates

    Special configuration options are:
      * topic: the MQTT topic to monitor for updates
      * qos: the MQTT quality of service (0-2) to use
    """

    def __init__(self, name, config):
        super().__init__('mqtt', name, config)

        if('qos' not in self.config):
            self.config['qos'] = 0

    def get_topic(self):
        return self.config['topic']

    def get_qos(self):
        return self.config['qos']

    def get_text(self):
        return self.config['template']

    def get_category(self):
        return constants.MQTT_CATEGORY
