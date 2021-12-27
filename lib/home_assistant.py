import requests
import json

class HomeAssistant:
    url = None
    token = None

    def __init__(self, url, token):
        self.url = url
        self.token = token

    def _makeRequest(self, endpoint):
        headers = {
            'Authorization': 'Bearer %s' % self.token,
            'content-type': 'application/json',
        }

        response = requests.get('%s%s' % (self.url,endpoint), headers=headers)

        return json.loads(response.text)

    def getStates(self, entity = ''):
        return self._makeRequest('/api/states/%s' % entity)

    def getState(self, entity = ''):
        return self.getStates(entity)
