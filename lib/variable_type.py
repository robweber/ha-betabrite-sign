from croniter import croniter
from datetime import datetime, timedelta
from termcolor import colored
from . import constants


class VariableType:
    """Defines the default VariableType class
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

    def render(self, text=''):
        """render the given text to be displayed on the command line
        :param text: the text to render

        :returns: the text with any termcolor markup applied
        """
        color = 'green' if 'color' not in self.config else self.config['color']
        return colored(text, color)

    def getName(self):
        """:returns: the name of this variable"""
        return self.name

    def getType(self):
        """:returns: the type of this variable """
        return self.type

    def getDisplayParams(self):
        """formats any display parameters for this variable
        so it can be sent to the alphasign as part of a String object

        :returns: properly formatted string with alphasign characters
        """
        result = ""

        if('color' in self.config):
            result = f"{constants.ALPHA_COLORS[self.config['color']]}"

        return result

    def getText(self):
        """:returns: the text for this variable as defined in yaml file"""
        return self.config['text']

    def getStartup(self):
        """:returns: the startup text for this variable as defined in the yaml file"""
        result = ""

        if('startup' in self.config):
            result = self.config['startup']

        return result

    @staticmethod
    def getCategory(self):
        """the category of this variable, implemented by subclasses"""
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

        # default poll time is every 5 min
        if 'cron' not in self.config:
            self.config['cron'] = "*/5 * * * *"

    def __findNext(self):
        cron = croniter(self.config['cron'])

        self.next_update = cron.get_next(datetime)

    def shouldPoll(self, current_time):
        result = False

        # base the next update on the time 1 min ago
        cron = croniter(self.config['cron'], current_time - timedelta(minutes=1))
        nextUpdate = cron.get_next(datetime)

        if(nextUpdate <= current_time):
            result = True

        return result

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
