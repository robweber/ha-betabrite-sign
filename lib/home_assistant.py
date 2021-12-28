import requests
import json


class HomeAssistant:
    """
    The HomeAssistant class is a simple class for the purposes
    of getting state and attribute information for different \
    entities from Home Assistant.
    """
    url = None
    token = None

    def __init__(self, url, token):
        """
        url is the fill url to an HA instance starting with http:// or http://
        token is a long lived access token created in HA
        """
        self.url = url
        self.token = token

    def _makeRequest(self, endpoint):
        headers = {
            'Authorization': 'Bearer %s' % self.token,
            'content-type': 'application/json',
        }

        response = requests.get('%s%s' % (self.url, endpoint), headers=headers)

        return json.loads(response.text)

    def getStates(self, entity=''):
        return self._makeRequest('/api/states/%s' % entity)

    def getState(self, entity=''):
        return self.getStates(entity)
