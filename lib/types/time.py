import datetime
from .. variable_type import AlphaSignVariable, PollingVariable
from .. import alphasign

class DateVariable(PollingVariable):
    dateSep = '/'

    def __init__(self, name, config):
        super().__init__('date', name, config)

        # allow for custom separator between date values
        if('seperator' in self.config):
            self.dateSep = self.config['separator']

    def getText(self):
        dateObj = datetime.datetime.today()

        return f"{dateObj.month}{self.dateSep}{dateObj.day}{self.dateSep}{dateObj.year}"

    def getStartup(self):
        return self.getText()

    def getPollTime(self):
        return 300

class TimeVariable(AlphaSignVariable):

    def __init__(self, name, config):
        super().__init__('time', name, config)

    def getText(self):
        timeObj = alphasign.time.Time()

        return timeObj

    def getStartup(self):
        return self.getText()
