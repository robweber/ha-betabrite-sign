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

from .. variable_type import PollingVariable


class HomeAssistantVariable(PollingVariable):
    """The Home Assistant variable type
    This is a polling type variable that that can pull from various
    HA entities as defined the yaml file

    Special configuration options are:
      * template: the home assistant template to render
    """
    def __init__(self, name, config):
        super().__init__('home_assistant', name, config)

    def get_text(self):
        return self.config['template']
