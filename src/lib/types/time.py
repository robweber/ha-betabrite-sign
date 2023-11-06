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

import alphasign
from datetime import datetime
from .. variable_type import AlphaSignVariable, PollingVariable


class DateVariable(PollingVariable):
    """A date variable type to display the current date on
    the sign.
    This is a polling type variable since it needs to be updated
    on the sign each day.

    Special configuration options in yaml are:
     * format: the format of the date string, using strftime, default  is mm/dd/yy
    """

    def __init__(self, name, config):
        super().__init__('date', name, config)

        # set the cron time to be at midnight each day
        # this is not a default so set after defaults merged
        self.config['cron'] = '0 0 * * *'

    def get_default_config(self):
        result = super().get_default_config()

        # add defaults for this class
        result['format'] = "%m/%d/%y"

        return result

    def get_text(self):
        dateObj = datetime.today()

        return dateObj.strftime(self.config['format'])

    def get_startup(self):
        return self.get_text()


class TimeVariable(AlphaSignVariable):
    """Represents the time object on the alphasign
    This is a special object in the alphasign protocol
    once it is set the sign will keep the time up to date

    Special configuration options in yaml are:
    * format: 12 or 24 if you want a standard or 24 hour clock.

    """
    def __init__(self, name, config):
        super().__init__('time', name, config)

    def get_default_config(self):
        result = super().get_default_config()

        # add defaults for this class
        result['format'] = 12

        return result

    def get_time_format(self):
        """get if this should be a 12 hr or 24 hour clock display

        :returns: a 0 or 1 depending on if a 12 or 24 hour clock
        """
        return 0 if self.config['format'] == 12 else 1

    def get_text(self):
        # create the alphasign Time object
        timeObj = alphasign.time.Time()

        return timeObj

    def get_startup(self):
        format = "%I:%M%p" if self.get_time_format() == 0 else "%H:%M"
        return datetime.now().strftime(format)
