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

    def get_text(self):
        dateObj = datetime.datetime.today()
        dateSep = self.config['separator']

        return f"{dateObj.month}{dateSep}{dateObj.day}{dateSep}{dateObj.year}"

    def get_startup(self):
        return self.get_text()


class TimeVariable(AlphaSignVariable):
    """Represents the time object on the alphasign
    This is a special object in the alphasign protocol
    once it is set the sign will keep the time up to date
    """
    def __init__(self, name, config):
        super().__init__('time', name, config)

    def get_text(self):
        # create the alphasign Time object
        timeObj = alphasign.time.Time()

        return timeObj

    def get_startup(self):
        return self.get_text()
