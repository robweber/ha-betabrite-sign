from .. import constants
from .. variable_type import VariableType


class MQTTVariable(VariableType):
    """The MQTT variable watches a specific MQTT topic for updates

    Special configuration options are:
      * topic: the MQTT topic to monitor for updates
      * qos: the MQTT quality of service (0-2) to use
      * parse_json: True/False value on if the payload contains JSON
    """

    def __init__(self, name, config):
        super().__init__('mqtt', name, config)

        if('parse_json' not in self.config):
            self.config['parse_json'] = False

        if('qos' not in self.config):
            self.config['qos'] = 0

    def get_topic(self):
        return self.config['topic']

    def get_qos(self):
        return self.config['qos']

    def parse_json(self):
        return self.config['parse_json']

    def get_text(self):
        return self.config['text']

    def get_category(self):
        return constants.MQTT_CATEGORY
