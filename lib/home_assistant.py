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
import json


class HomeAssistant:
    """The HomeAssistant class is a simple class for the purposes
    of getting state and attribute information for different
    entities from Home Assistant.
    """
    url = None
    token = None

    def __init__(self, url, token):
        """
        :param url: the url to an HA instance starting with http:// or http://
        :param token: a long lived access token created in HA
        """
        self.url = url
        self.token = token

    def _make_request(self, endpoint, data=None):
        """makes the request to the given HA endpoint

        :returns: the HTTP response HTTP object
        """
        headers = {
            'Authorization': 'Bearer %s' % self.token,
            'content-type': 'application/json',
        }

        # if no POST data given, do a GET request
        if(data is None):
            response = requests.get('%s%s' % (self.url, endpoint), headers=headers)
        else:
            response = requests.post('%s%s' % (self.url, endpoint), data=json.dumps(data), headers=headers)

        return response

    def get_state(self, entity=''):
        """get the state of a specific HA entity

        :param entity: the entity name in Home Assistant you want to get the state of

        :returns: a dict containing the state of this entity
        """
        response = self._make_request('/api/states/%s' % entity)

        return json.loads(response.text)

    def render_template(self, template):
        """sends a template string to Home Assistant to have it rendered

        :param template: the string as a valid HA template

        :returns: the response from Home Assistant as a string
        """
        result = None
        response = self._make_request('/api/template', {'template': template})

        if(response.status_code == 200):
            # successful template rendering
            result = response.text
        else:
            errorJson = json.loads(response.text)
            raise TemplateSyntaxError(errorJson['message'])

        return result


class TemplateSyntaxError(Exception):
    """Exception to catch when an HA templated message has incorrect syntax
    thrown by the HomeAssistant class upon unsuccessful template rendering
    as indicated in the response from HA
    """
    def __init__(self, message):
        super().__init__(f"Template cannot be rendered: {message}")
