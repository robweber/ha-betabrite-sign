from .. import constants
from .. variable_type import VariableType


class MQTTVariable(VariableType):
    """The MQTT variable watches a specific MQTT topic for updates

    Special configuration options are:
      * topic: the MQTT topic to monitor for updates
      * parse_json: True/False value on if the payload contains JSON
    """

    def __init__(self, name, config):
        super().__init__('mqtt', name, config)

        if('parse_json' not in self.config):
            self.config['parse_json'] = False

    def getTopic(self):
        return self.config['topic']

    def parseJson(self):
        return self.config['parse_json']

    def getText(self):
        return self.config['text']

    def getCategory(self):
        return constants.MQTT_CATEGORY
