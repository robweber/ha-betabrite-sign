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

import requests
import unicodedata
from .. import constants
from .. variable_type import JinjaVariable, PollingVariable


class RestVariable(JinjaVariable, PollingVariable):
    """A REST variable type
    This is a polling type variable that that will pull from a
    web address as either a GET or POST type request

    Special configuration options are:
      * url: the home assistant template to render
      * method: GET or POST
    """
    def __init__(self, name, config):
        super().__init__('rest', name, config)

    def get_default_config(self):
        result = super().get_default_config()

        # add defaults for this class
        result['method'] = 'get'

        return result

    def poll(self):
        result = ''

        # make the request based on the method given
        if(self.config['method'].lower() == 'get'):
            response = requests.get(self.config['url'])
        else:
            response = requests.post(self.config['url'])

        if(response.status_code == 200):
            # successful request
            result = unicodedata.normalize('NFD', response.text)

        return result

    def get_text(self):
        return self.config['template']

    def get_categories(self):
        return [constants.POLLING_CATEGORY, constants.JINJA_CATEGORY]
