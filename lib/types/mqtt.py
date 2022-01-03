from .. import constants
from .. variable_type import VariableType


class MQTTVariable(VariableType):
    """The MQTT variable watches a specific MQTT topic for updates

    Special configuration options are:
      * topic: the MQTT topic to monitor for updates
    """
    def __init__(self, name, config):
        super().__init__('mqtt', name, config)

    def getTopic(self):
        return self.config['topic']

    def getText(self):
        return self.config['text']

    def getCategory(self):
        return constants.MQTT_CATEGORY
