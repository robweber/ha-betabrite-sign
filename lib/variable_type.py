from croniter import croniter
from datetime import datetime
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

    def get_name(self):
        """:returns: the name of this variable"""
        return self.name

    def get_type(self):
        """:returns: the type of this variable """
        return self.type

    def get_display_params(self):
        """formats any display parameters for this variable
        so it can be sent to the alphasign as part of a String object

        :returns: properly formatted string with alphasign characters
        """
        result = ""

        if('color' in self.config):
            result = f"{constants.ALPHA_COLORS[self.config['color']]}"

        if('font' in self.config):
            result = f"{result}{constants.ALPHA_FONTS[self.config['font']]}"

        return result

    def get_text(self):
        """:returns: the text for this variable as defined in yaml file"""
        return self.config['text']

    def get_startup(self):
        """:returns: the startup text for this variable as defined in the yaml file"""
        result = ""

        if('startup' in self.config):
            result = self.config['startup']

        return result

    @staticmethod
    def get_category(self):
        """the category of this variable, implemented by subclasses"""
        raise NotImplementedError


class PollingVariable(VariableType):
    """
    Represents a VariableType class that updates its
    data through polling, variables of this type
    need to specify a polling interval as a cron expression
    using the "cron" parameter in the YAML config, if missing
    it will default to every 5 minutes
    """

    def __init__(self, type, name, config):
        super().__init__(type, name, config)

        # default poll time is every 5 min
        if 'cron' not in self.config:
            self.config['cron'] = "*/5 * * * *"

    def should_poll(self, current_time, offset):
        """decides if this variable should be updated based on
        the configured cron expression. This is done using the current
        time and an offset to decide. Doing it this way ensures a valid "next update"
        time can be calculated.

        For example, if the next update time is calculated from the current time
        (datetime.now()) the cron expression will always happen in the future. By
        subtracting a slight offset (usually 1 min) we can determine if the current
        time has passed, or is equal to, when this variable should next be polled. This
        allows for arbitrary time comparisons as well as avoids storing the last updated time

        :param current_time: a datetime object that represents the time to
        compare against, usually the current time (datetime.now())
        :param offset: timedelta representing the offset to subtract from current time
        :returns: True/False if the variable should be updated
        """
        result = False

        # base the next update on the offset as the start time
        cron = croniter(self.config['cron'], current_time - offset)
        nextUpdate = cron.get_next(datetime)

        if(nextUpdate <= current_time):
            result = True

        return result

    def get_category(self):
        return constants.POLLING_CATEGORY


class AlphaSignVariable(VariableType):
    """
    Special variable category that uses built-in
    Alphasign protocol objects to display data
    """

    def __init__(self, type, name, config):
        super().__init__(type, name, config)

    def get_category(self):
        return constants.ALPHASIGN_CATEGORY
