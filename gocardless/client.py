import base64
import datetime
import json
import logging
import os
import urllib

import gocardless
import urlbuilder
from gocardless.utils import generate_signature, to_query
from gocardless.request import Request
from gocardless.exceptions import ClientError, SignatureError
from gocardless.resources import Merchant, Subscription, Bill, PreAuthorization, User

logger = logging.getLogger(__name__)

class Client(object):

    API_PATH = '/api/v1'

    BASE_URLS = {
      'production': 'https://gocardless.com',
      'sandbox': 'https://sandbox.gocardless.com',
    }

    base_url = None

    @classmethod
    def get_base_url(cls):
        """
        Return the correct base URL for the current environment. If one has
        been manually set, default to that.
        """
        return cls.base_url or cls.BASE_URLS[gocardless.environment]

    def __init__(self, **account_details):
        if 'app_id' not in account_details:
            raise ValueError('You must provide an app_id')

        if 'app_secret' not in account_details:
            raise ValueError('You must provide an app_secret')

        if "token" not in account_details:
            raise ValueError("You must provide an access token")

        self._app_id = account_details['app_id']
        self._app_secret = account_details['app_secret']
        self._access_token = account_details.get('token')
        self._merchant_id = account_details.get('merchant_id')

    def api_get(self, path, **kwargs):
        """
        Issue an GET request to the API server.

        :param path: the path that will be added to the API prefix
        """
        return self._request('get', Client.API_PATH + path, **kwargs)

    def api_post(self, path, data, **kwargs):
        """Issue a PUT request to the API server

        :param path: The path that will be added to the API prefix
        :param data: The data to post to the url.
        """
        self.set_payload(data)
        return self._request('post', Client.API_PATH + path, **kwargs)

    def _request(self, method, path, **kwargs):
        """
        Send a request to the GoCardless API servers.

        :param method: the HTTP method to use (e.g. +:get+, +:post+)
        :param path: the path fragment of the URL
        """
        logger.debug("Executing request to path {0}".format(path))
        request_url = Client.get_base_url() + path
        request = Request(method, request_url)

        if 'auth' in kwargs:
            # If using HTTP basic auth, let requests handle it
            request.use_http_auth(kwargs['auth'])
        else:
            # Default to using bearer auth with the access token
            request.use_bearer_auth(self._access_token)

        request.set_payload(kwargs.get('data'))        
        response = request.perform()
        if type(response) == dict and "error" in response.keys():
            raise ClientError("Error calling api, message was {0}".format(
                response["error"]))
        return response
        
    def merchant(self):
        """
        Returns the current Merchant's details.
        """
        return Merchant(self.api_get('/merchants/%s' % self._merchant_id), self)
    
    def users(self):
        """
        Index a merchant's customers 
        """
        return self.api_get('/merchants/%s/users' % self._merchant_id)

    def user(self, id):
        """
        Find a user by id
        """
        return User.find_with_client(id, self)

    def pre_authorization(self, id):
        """
        Find a pre authorization with id `id`
        """
        return PreAuthorization.find_with_client(id, self)
    
    def subscription(self, id):
        """
        Returns a single subscription
        """
        return Subscription.find_with_client(id, self)

    def bill(self, id):
        """
        Find a bill with id `id`
        """
        return Bill.find_with_client(id, self)

    def new_subscription_url(self, amount, interval_length, interval_unit, 
            name=None, description=None, interval_count=None, start_at=None,
            expires_at=None, redirect_uri=None, cancel_uri=None, state=None):
        """Generate a url for creating a new subscription

        :param amount: The amount to charge each time
        :param interval_length: The length of time between each charge, this
        is an integer, the units are specified by interval_unit.
        :param interval_unit: The unit to measure the interval length, must
        be one of "day' or "week"
        :param name: The name to give the suvscription
        :param description: The description of the subscription
        :param interval_count: The Calculates expires_at based on the number
        of intervals you would like to collect. If both interval_count and
        expires_at are specified the expires_at parameter will take 
        precedence 
        :param expires_at: When the subscription expires, should be a datetime
        object.
        :param starts_at: When the subscription starts, should be a datetime
        object
        :param redirect_uri: URI to redirect to after the authorization process
        :param cancel_uri: URI to redirect the user to if they cancel
        authorization
        :param state: String which will be passed to the merchant on
        redirect.
        """
        params = urlbuilder.SubscriptionParams(amount, self._merchant_id, 
                interval_length, interval_unit, name=name, 
                description=description, interval_count=interval_count, 
                expires_at=expires_at, start_at=start_at)
        builder = urlbuilder.UrlBuilder(self)
        return builder.build_and_sign(params, redirect_uri=redirect_uri, 
                cancel_uri=cancel_uri, state=state)

        
    def new_bill_url(self, amount, name=None, description=None,
            redirect_uri=None, cancel_uri=None, state=None):
        """Generate a url for creating a new bill

        :param amount: The amount to bill the customer
        :param name: The name of the bill
        :param description: The description of the bill
        :param redirect_uri: URI to redirect to after the authorization process
        :param cancel_uri: URI to redirect the user to if they cancel
        authorization
        :param state: String which will be passed to the merchant on
        redirect.

        """
        params = urlbuilder.BillParams(amount, self._merchant_id, name=name, 
                description=description)
        builder = urlbuilder.UrlBuilder(self)
        return builder.build_and_sign(params, redirect_uri=redirect_uri, 
                cancel_uri=cancel_uri, state=state)
        
    def new_preauthorization_url(self,max_amount, interval_length,\
            interval_unit, expires_at=None, name=None, description=None,\
            interval_count=None, calendar_intervals=None,
            redirect_uri=None, cancel_uri=None, state=None):
        """Get a url for creating new pre_authorizations

        :param max_amount: A float which is the maximum amount for this
        pre_authorization
        :param interval_length: The length of this pre_authorization
        :param interval_unit: The units in which the interval_length
        is measured, must be one of
        - "day"
        - "month"
        :param expires_at: The date that this pre_authorization will
        expire, must be a datetime object which is in the future.
        :param name: A short string which is the name of the pre_authorization
        :param description: A longer string describing what the 
        pre_authorization is for.
        :param interval_count: calculates expires_at based on the number of
        payment intervals you would like the resource to have. Must be a
        positive integer greater than 0. If you specify both an interval_count
        and an expires_at argument then the expires_at argument will take
        precedence.
        :param calendar_intervals: Describes whether the interval resource
        should be aligned with calendar weeks or months, default is False
        :param redirect_uri: URI to redirect to after the authorization process
        :param cancel_uri: URI to redirect the user to if they cancel
        authorization
        :param state: String which will be passed to the merchant on
        redirect.

        """
        params = urlbuilder.PreAuthorizationParams(max_amount, self._merchant_id, \
            interval_length, interval_unit, expires_at=expires_at, name=name, description=description,\
            interval_count=interval_count, calendar_intervals=calendar_intervals)
        builder = urlbuilder.UrlBuilder(self)
        return builder.build_and_sign(params, redirect_uri=redirect_uri, 
                cancel_uri=cancel_uri, state=state)

    def confirm_resource(self, params):
        """Confirm a payment

        This send a post request to the confirmation URI for a payment.
        params should contain these elements from the request
        - resource_uri
        - resource_id
        - resource_type
        - signature
        - state (if any)
        """
        keys = ["resource_uri", "resource_id", "resource_type", "state"]
        to_check = dict([[k,v] for k,v in params.items() if k in keys])
        signature = generate_signature(to_check, self._app_secret)
        if not signature == params["signature"]:
            raise SignatureError("Invalid signature when confirming resource")
        auth_string = base64.b64encode("{0}:{1}".format(
            self._app_id, self._app_secret))
        to_post = {
                "resource_id":params["resource_id"],
                "resource_type":params["resource_type"]
                }
        self.api_post(params["resource_uri"], to_post, auth=auth_string)
        
    def new_merchant_url(self, redirect_uri, state=None):
        """Get a URL for managing a new merchant

        This method creates a URL which partners should redirect
        merchants to in order to obtain permission to manage their GoCardless
        payments.
        :param redirect_uri: The URI where the merchant will be sent after
        authorizing.
        :param state: An optional string which will be present in the request
        to the redirect URI, useful for tracking the user.
        """
        params = {
                "client_id":self._app_id,
                "redirect_uri":redirect_uri,
                "scope":"manage_merchant",
                "response_type":"code"
                }
        if state:
            params["state"] = state
        return "{0}/oauth/authorize?{1}".format(self.get_base_url(),
                to_query(params))

    def fetch_access_token(self, redirect_uri, authorization_code):
        """Fetch the access token for a merchant

        Takes the authorization code obtained from a merchant redirect
        and the redirect_uri used in that same redirect and fetches the
        corresponding access token. The access token is returned and also
        set on the client so the client can then be used to make api calls
        on behalf of the merchant.

        :param redirect_uri: The redirect_uri used in the request which 
        obtained the authorization code, must match exactly.
        :param authorization_code: The authorization code obtained in the
        previous part of the process.
        """
        params = {
                "client_id":self._app_id,
                "code":authorization_code,
                "redirect_uri":redirect_uri,
                "grant_type":"authorization_code"
                }
        auth = base64.b64encode("{0}:{1}".format(self._app_id, 
            self._app_secret))
        url = "{0}/oauth/access_token".format(self.get_base_url())
        result =  self.api_post(url, params, auth=auth)
        self._token = result["access_token"]
        self._merchant_id = result["scope"].split(":")[1]
        return self._token





