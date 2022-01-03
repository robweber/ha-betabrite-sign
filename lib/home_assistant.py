import requests
import json
from json.decoder import JSONDecodeError


class HomeAssistant:
    """The HomeAssistant class is a simple class for the purposes
    of getting state and attribute information for different \
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

    def _makeRequest(self, endpoint, data=None):
        """makes the request to the given HA endpoint

        :returns: string containing the response from Home Assistant
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

        return response.text

    def getState(self, entity=''):
        """
        :param entity: the entity name in Home Assistant you want to get the state of

        :returns: a dict containing the state of this entity
        """
        return json.loads(self._makeRequest('/api/states/%s' % entity))

    def renderTemplate(self, template):
        """sends a template string to Home Assistant to have it rendered

        :param template: the string as a valid HA template

        :returns: the response from Home Assistant as a string
        """
        result = self._makeRequest('/api/template', {'template': template})

        try:
            # if this works we likely have an error
            errorJson = json.loads(result)

            raise TemplateSyntaxError(errorJson['message'])
        except JSONDecodeError:
            # do nothing here, this should fail if working
            pass

        return result


class TemplateSyntaxError(Exception):
    """Exception to catch when an HA templated message has incorrect syntax
    thrown by the HomeAssistant class upon unsuccessful template rendering
    as indicated in the response from HA
    """
    def __init__(self, message):
        super().__init__(f"Template cannot be rendered: {message}")
