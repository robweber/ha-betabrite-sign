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
from .. variable_type import TemplateVariable


class MQTTVariable(TemplateVariable):
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

    def get_topic(self):
        return self.config['topic']

    def get_qos(self):
        return self.config['qos']
