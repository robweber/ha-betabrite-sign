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
from .. variable_type import JinjaVariable, StatefulVariable


class MQTTVariable(JinjaVariable):
    """The MQTT variable watches a specific MQTT topic for updates

    Special configuration options are:
      * topic: the MQTT topic to monitor for updates
      * qos: the MQTT quality of service (0-2) to use
    """

    def __init__(self, name, config):
        super().__init__('mqtt', name, config)

    def get_topic(self):
        return self.config['topic']

    def get_qos(self):
        return self.config['qos']

    def get_categories(self):
        return [constants.MQTT_CATEGORY, constants.JINJA_CATEGORY]

class MQTTPushVariable(MQTTVariable):
    """extension of the MQTT class allows for listening to
    and publishing to an MQTT topic

    Special configuration options are:
      * topic: the MQTT topic to monitor or publish to
      * qos: the MQTT quality of service (0-2) to use
      * should_update_topic_template: eval True/False on if a new value should be published
      * update_topic_template: template to render new value to publish

    """
    def __init__(self, name, config):
        super().__init__(name, config)
        self.type = "mqtt_push"  # override type

    def should_update_topic(self):
        return self.config['should_update_topic_template']

    def update_topic(self):
        return self.config['update_topic_template']

    def get_categories(self):
        return [constants.MQTT_CATEGORY, constants.JINJA_CATEGORY, constants.MQTT_PUSH_CATEGORY]

class TimerVariable(MQTTPushVariable, StatefulVariable):
    """ Internal class to implement a countdown timer.
    This class implements polling, mqtt, stateful, and jinja behaviors

    Overview of innner workings:
    * The internal state is kept track of via updates from MQTT topics
    * Activating the time sets internal state to running
    * Sign updates handled via polling (should_poll=true when timer is running)
    * Rendering template calculates time remaining based on set end time
    * When timer complete mqtt value is published to indicate timer stopped

    """

    def __init__(self, name, config):
        super().__init__(name, config)
        self.type = 'timer' # override type

    def get_default_config(self):
        result = super().get_default_config()

        # template to render time remaining from payload
        # if timer running result is HH:MM:SS
        result['template'] = """
        {% if(value.running) %}
        {% set remaining = value.end_time - now() %}
        {% set total_seconds = remaining.total_seconds() | int %}
        {% if total_seconds > 0 %}
        {% set minutes = (total_seconds / 60) | int %}
        {% set hours = (minutes / 60) | int %}
        {{ "{:02d}".format(hours) }}:{{ "{:02d}".format(minutes) }}:{{ "{:02d}".format(((total_seconds % 60) % 60) | int) }}
        {% else %}
        !!!Timer Complete!!!
        {% endif %}
        {% endif %}
        """

        # update the topic if running and timer is expired
        # 1 minute added to eval to make sure complete message displays for at least one minute
        result['should_update_topic_template'] = """
        {% if(value.running) %}
        {% set remaining = (value.end_time + timedelta(minutes=1)) - now() %}
        {% set total_seconds = remaining.total_seconds() | int %}
        {{ total_seconds <= 0 }}
        {% else %}
        False
        {% endif %}
        """
        # return value for MQTT topic - ON/OFF depending on running status
        result['update_topic_template'] = """
        {% set remaining = value.end_time - now() %}
        {% set total_seconds = remaining.total_seconds() | int %}
        {% if(value.running and total_seconds > 0) %}
        ON
        {% else %}
        OFF
        {% endif %}
        """

        # timer off on startup, default timer to 5 minutes
        result['states'] = {"running": False, "timer": {"hours":0, "minutes": 5}}

        return result

    def should_poll(self, current_time, offset):
        """ override of parent class should_poll method

        For this class it will always return true if timer is running and
        false if the timer is not running
        """

        return self._states['running']

    def get_categories(self):
        return [constants.MQTT_CATEGORY, constants.JINJA_CATEGORY, constants.MQTT_PUSH_CATEGORY,
                constants.STATEFUL_CATEGORY, constants.POLLING_CATEGORY]
