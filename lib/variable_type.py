
# default variable type object
class VariableType:
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

# variables that are updated via polling
class PollingVariable(VariableType):

    def __init__(self, type, name, config):
        super().__init__(type, name, config)

    def getPollTime(self):
        return self.config['poll_time']

    def getCategory(self):
        return 'polling'

# variables that are part of alphasign protocol
class AlphaSignVariable(VariableType):

    def __init__(self, type, name, config):
        super().__init__(type, name, config)

    def getCategory(self):
        return 'alphasign'
