from .. variable_type import PollingVariable


class HomeAssistantVariable(PollingVariable):
    """The Home Assistant variable type
    This is a polling type variable that that can pull from various
    HA entities as defined the yaml file

    Special configuration options are:
      * template: the home assistant template to render
    """
    def __init__(self, name, config):
        super().__init__('home_assistant', name, config)

    def getText(self):
        return self.config['template']
