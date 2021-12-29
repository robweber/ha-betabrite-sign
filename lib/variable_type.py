from . import constants

class VariableType:
    """
    Defines the default VariableType class
    this is mean to be subclassed by different implementing
    variable categories
    """
    type = None
    name = None
    config = None

    def __init__(self, type, name, config):
        self.type = type
        self.name = name
        self.config = config

    def getName(self):
        return self.name

    def getType(self):
        return self.type

    def getDisplayParams(self):
        result = ""

        if('color' in self.config):
            result = f"{constants.ALPHA_COLORS[self.config['color']]}"

        return result

    def getText(self):
        return self.config['text']

    def getStartup(self):
        result = ""

        if('startup' in self.config):
            result = self.config['startup']

        return result

    @staticmethod
    def getCategory(self):
        raise NotImplementedError


class PollingVariable(VariableType):
    """
    Represents a VariableType class that updates its
    data through polling, variables of this type
    need to specify a polling interval through the
    "poll_time" parameter in the YAML config
    """

    def __init__(self, type, name, config):
        super().__init__(type, name, config)

    def getPollTime(self):
        return self.config['poll_time']

    def getCategory(self):
        return constants.POLLING_CATEGORY


class AlphaSignVariable(VariableType):
    """
    Special variable category that uses built-in
    Alphasign protocol objects to display data
    """

    def __init__(self, type, name, config):
        super().__init__(type, name, config)

    def getCategory(self):
        return constants.ALPHASIGN_CATEGORY
