import alphasign
import datetime
from .. variable_type import AlphaSignVariable, PollingVariable


class DateVariable(PollingVariable):
    """A date variable type to display the current date on
    the sign.
    This is a polling type variable since it needs to be updated
    on the sign each day.

    Special configuration options in yaml are:
     * separator: the separator character between the date fields
    """

    def __init__(self, name, config):
        super().__init__('date', name, config)

        # allow for custom separator between date values
        if('separator' not in self.config):
            self.config['separator'] = '/'

        # set the cron time to be at midnight each day
        self.config['cron'] = '0 0 * * *'

    def getText(self):
        dateObj = datetime.datetime.today()
        dateSep = self.config['separator']

        return f"{dateObj.month}{dateSep}{dateObj.day}{dateSep}{dateObj.year}"

    def getStartup(self):
        return self.getText()


class TimeVariable(AlphaSignVariable):
    """Represents the time object on the alphasign
    This is a special object in the alphasign protocol
    once it is set the sign will keep the time up to date
    """
    def __init__(self, name, config):
        super().__init__('time', name, config)

    def getText(self):
        # create the alphasign Time object
        timeObj = alphasign.time.Time()

        return timeObj

    def getStartup(self):
        return self.getText()
