from .. variable_type import PollingVariable


class HomeAssistantVariable(PollingVariable):
    """The Home Assistant variable type
    This is a polling type variable that that can pull from various
    HA entities as defined the yaml file

    Special configuration options are:
      * entities: list of entities to poll for this variable
    """
    def __init__(self, name, config):
        super().__init__('home_assistant', name, config)

    def getEntities(self):
        """:returns: list of HA entities within scope of this variable"""
        return self.config['entities']
