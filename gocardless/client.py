import json

import gocardless
from .request import Request
from .exceptions import ClientError


class Client(object):

    API_PATH = '/api/v1'

    BASE_URLS = {
      'production': 'https://gocardless.com',
      'sandbox': 'https://sandbox.gocardless.com',
    }

    base_url = None

    @classmethod
    def get_base_url(cls):
        """Return the correct base URL for the current environment. If one has
        been manually set, default to that.
        """
        return cls.base_url or cls.BASE_URLS[gocardless.environment]

    def __init__(self, **account_details):
        if 'app_id' not in account_details:
            raise ValueError('You must provide an app_id')

        if 'app_secret' not in account_details:
            raise ValueError('You must provide an app_secret')

        self._app_id = account_details['app_id']
        self._app_secret = account_details['app_secret']
        self._access_token = account_details.get('token')
        self._merchant_id = account_details.get('merchant_id')

    def api_get(self, path, **kwargs):
        """Issue an GET request to the API server.

        :param path: the path that will be added to the API prefix
        :param params: query string parameters
        """
        return self._request('get', Client.API_PATH + path, **kwargs)

    def _request(self, method, path, **kwargs):
        """Send a request to the GoCardless API servers.

        :param method: the HTTP method to use (e.g. +:get+, +:post+)
        :param path: the path fragment of the URL
        """
        request_url = Client.get_base_url() + path
        request = Request(method, request_url)

        if 'auth' in kwargs:
            # If using HTTP basic auth, let requests handle it
            request.use_http_auth(kwargs['auth'])
        else:
            # Default to using bearer auth with the access token
            request.use_bearer_auth(self._access_token)

        request.set_payload(kwargs.get('data'))        
        return request.perform()
        
    def merchant(self):
        """Returns the current Merchant's details.
        
        """
        return self.api_get('/merchants/%s' % self._merchant_id)
    
    def users(self):
        """Index a merchant's customers 
        """
        return self.api_get('/merchants/%s/users' % self._merchant_id)
    
    
    def subscriptions(self):
        """Returns all subscriptions for a merchant."""
        return self.api_get('/merchants/%s/subscriptions/' % self._merchant_id)


    def get_subscription(self, id):
        """Returns a single subscription
        """
        return self.api_get('/subscriptions/%s' % (id))
    
    def cancel_subscription(self, id):
        """Cancels a subscription given an id"""
        


