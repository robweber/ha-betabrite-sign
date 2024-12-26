"""
Copyright 2024 Rob Weber
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

from .. import constants
from .. variable_type import AlphaSignVariable, JinjaVariable, PollingVariable


class DynamicVariable(JinjaVariable, PollingVariable):
    """Variable type that holds dynamic text
    This is typically combined from other variable types

    Template content is rendered once per minute (polling) or when variables referenced
    in the template are changed
    """
    def __init__(self, name, config):
        super().__init__('dynamic', name, config)

        # set the cron time to be at midnight each day
        # this not changeable so set after defaults merged
        self.config['cron'] = '*/1 * * * *'

    def get_categories(self):
        return [constants.POLLING_CATEGORY, constants.JINJA_CATEGORY]


class StaticVariable(AlphaSignVariable):
    """Variable type that holds static text
    Once this is sent to the sign it is not updated again
    """
    def __init__(self, name, config):
        super().__init__('static', name, config)

    def get_startup(self):
        return self.get_text()
