import datetime
from .. variable_type import AlphaSignVariable, PollingVariable
from .. import alphasign

class DateVariable(PollingVariable):

    def __init__(self, name, config):
        super().__init__('date', name, config)

    def getText(self):
        dateObj = datetime.datetime.today()

        return f"{dateObj.month}-{dateObj.day}-{dateObj.year}"

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
