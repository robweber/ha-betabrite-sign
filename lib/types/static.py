from .. variable_type import AlphaSignVariable
from .. import alphasign

class StaticVariable(AlphaSignVariable):

    def __init__(self, name, config):
        super().__init__('static', name, config)

    def getText(self):
        return self.config['text']

    def getStartup(self):
        return self.getText()
