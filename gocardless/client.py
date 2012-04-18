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

    def api_delete(self, path, **kwargs):
        """Issue a delete to the API server.

        :param path: the path that will be added to the API prefix
        :param params: query string parameters
        """
        return self._request('delete', Client.API_PATH + path, **kwargs)

     def api_put(self, path, **kwargs):
        """Issue a PUT to the API server.

        :param path: the path that will be added to the API prefix
        :param params: query string parameters
        """
        return self._request('put', Client.API_PATH + path, **kwargs)


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
    
    def users(self, **kwargs):
        """Index a merchant's customers 
        """
        return self.api_get('/merchants/%s/users' % self._merchant_id, **kwargs)
    
    
    def subscriptions(self, **kwargs):
        """Returns all subscriptions for a merchant."""
        return self.api_get('/merchants/%s/subscriptions/' % self._merchant_id, **kwargs)


    def get_subscription(self, id):
        """Returns a single subscription.

        :params : id - Subscription ID
        """
        return self.api_get('/subscriptions/%s' % (id))
    
    def cancel_subscription(self, id):
        """Cancels a subscription given an id.

        :params id:  Subscription ID

        """
        return self.api_put('/subscriptions/%s/cancel/' % (id))

    def get_pre_auth(self, id):
        """Show one pre-authorisation.
        :params id: pre-auth id

        """
        return self.api_get('/pre_authorizations/%s' % (id))
        
    def pre_auths(self, **kwargs):
        """Returns a list of a merchants pre-authorised transactions.
        """
        return self.api_get('/merchants/%s/pre_authorizations'% (self._merchant_id), **kwargs)

    def get_bill(self, id):
        """Returns a single Bill object.

        :params id: Bill id
        """
        return self.api_get('/bills/%' % (id))

    def bills(self, **kwargs):
        """Returns all Bills for a merchant.
        """
        return self.api_get('/merchant/%s/bills' % (self._merchant_id), **kwargs)

    def create_bill(self, amount, pre_auth_id):
        """Create a new bill against an existing pre_authorization, if and only if
        the pre_auth has not expired.
        
        :params amount: Amount to be billed in float to two significant figures.
        :params pre_auth_id: A valid pre authorisation id.
        """
        payload = {"bill": {"amount": amount, "pre_authorization_id": pre_auth_id}}
        return self._request('post', '/bills', data=json.dumps(payload))

