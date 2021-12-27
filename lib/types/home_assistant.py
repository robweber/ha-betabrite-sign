from .. variable_type import PollingVariable

class HomeAssistantVariable(PollingVariable):

    def __init__(self, name, config):
        super().__init__('home_assistant', name, config)
