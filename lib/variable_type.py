"""
Copyright 2022 Rob Weber
This file is part of ha-betabrite-sign
omni-epd is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging
import re
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
        """
        :param type: the type of variable, unique to subclasses
        :param name: the name of the variable, as defined by the user in yaml file
        :param config: a dict containing the config as read from the yaml file
        """
        self.type = type
        self.name = name

        # get the defaults for this variable
        defaults = self.get_default_config()

        # set defaults and override with user values
        self.config = defaults.copy()
        self.config.update(config)

    def get_name(self):
        """:returns: the name of this variable"""
        return self.name

    def get_type(self):
        """:returns: the type of this variable """
        return self.type

    def get_default_config(self):
        """ get default config for this class' categories
        can be overriden by child classes that need additional defaults

        :returns: dict of default config options for this class
        """
        result = {}
        for c in self.get_categories():
            result.update(constants.CATEGORY_DEFAULTS[c])
        return result

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

    def get_categories(self):
        """the categories of this variable, implemented by subclasses"""
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

    def get_categories(self):
        return [constants.POLLING_CATEGORY]


class AlphaSignVariable(VariableType):
    """
    Special variable category that uses built-in
    Alphasign protocol objects to display data
    """

    def __init__(self, type, name, config):
        super().__init__(type, name, config)

    def get_categories(self):
        return [constants.ALPHASIGN_CATEGORY]


class JinjaVariable(VariableType):
    """a variable type that can render Jinja templates from the payload
    Special configuration options are:
      * template: what to render on the sign
      * update_template: eval True/False if this template should be updated
    """
    __depends = None

    def __init__(self, type, name, config):
        super().__init__(type, name, config)

        # get variables this var depends on based on 'get_payload' or 'is_payload' type functions
        # uses matching per description https://docs.python.org/3/library/re.html#re.findall
        self.__depends = []
        matches = re.findall("(is_payload(_attr)?\('(\w+)',)|(get_payload(_attr)?\('(\w+)'(,)?)", self.get_text())  # noqa: W605
        for m in matches:
            # will be in group 2 or 5
            depend = m[2] if m[2] != '' else m[5]
            if(depend not in self.__depends):
                self.__depends.append(depend)

        if(len(self.__depends) > 0):
            logging.debug(f"{name} dependencies: {self.__depends}")

    def get_dependencies(self):
        return self.__depends

    def update_template(self):
        return self.config['update_template']

    def get_text(self):
        return self.config['template']

    def get_categories(self):
        return [constants.JINJA_CATEGORY]
