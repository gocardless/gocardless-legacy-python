import gocardless
import json
import requests


class Request(object):

    def __init__(self, method, url):
        self._method = method
        self._url = url
        headers = {}
        headers["Accept"] = "application/json"
        headers["User-Agent"] = "gocardless-python/{0}".format(gocardless.get_version())
        self._opts = {"headers" : headers }

        if not self._valid_method(method):
            raise ValueError('Invalid method {}'.format(method))

    def _valid_method(self, method):
        return method in ('get', 'post', 'put')

    def use_http_auth(self, username, password):
        self._opts['auth'] = (username, password)

    def use_bearer_auth(self, token):
        auth_header = 'bearer {}'.format(token)
        self._opts['headers']['Authorization'] = auth_header

    def set_payload(self, payload):
        if payload is not None:
            # Set the payload type - always JSON
            self._opts['headers']['Content-Type'] = 'application/json'
            # And JSON encode the data
            self._opts['data'] = json.dumps(payload)

    def perform(self):
        fetch_func = getattr(requests, self._method)
        response = fetch_func(self._url, **self._opts)
        return json.loads(response.content)

