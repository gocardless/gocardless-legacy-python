import base64
import logging

import gocardless
from gocardless import urlbuilder
from gocardless.utils import generate_signature, to_query, signature_valid
from gocardless.request import Request
from gocardless.exceptions import ClientError, SignatureError
from gocardless.resources import (Merchant, Subscription, Bill,
                                  PreAuthorization, User, Payout)

import six

logger = logging.getLogger(__name__)

API_PATH = '/api/v1'
BASE_URLS = {
    'production': 'https://gocardless.com',
    'sandbox': 'https://sandbox.gocardless.com',
}


class Client(object):
    """The main interface to the GoCardless API

    This class is the starting point for interacting with GoCardless.
    If you are a merchant than you can obtain a client instance by setting
    your account details in :py:func:`gocardless.set_details`.

    If you are a
    partner and need OAuth access to other merchants' accounts then you need
    to create a client using your app id and app secret, then use the OAuth
    APIs to obtain authorization over the merchants' account.

    """

    base_url = None

    @classmethod
    def get_base_url(cls):
        """
        Return the correct base URL for the current environment. If one has
        been manually set, default to that.
        """
        return cls.base_url or BASE_URLS[gocardless.environment]

    def __init__(self, app_id, app_secret, access_token=None,
                 merchant_id=None):
        """Create a client

        :param string app_id: Your application id.
        :param string app_secret: Your app secret.
        :param string access_token: The access token for this account, this
            should be your access token from the developer settings page unless
            you are trying to manage another merchants' account via OAuth.
        :param string merchant_id: The merchant id for this account, should be
            your merchant id unless you are trying to manage another account
            via OAuth.
        """
        self._app_id = app_id
        self._app_secret = app_secret
        if access_token:
            self._access_token = access_token
        if merchant_id:
            self._merchant_id = merchant_id

    def api_get(self, path, params=None, **kwargs):
        """
        Issue an GET request to the API server.

        :param path: the path that will be added to the API prefix
        :param params: query string parameters
        """
        return self._request('get', API_PATH + path, params=params, **kwargs)

    def api_post(self, path, data, **kwargs):
        """Issue a POST request to the API server

        :param path: The path that will be added to the API prefix
        :param data: The data to post to the url.
        """
        return self._request('post', API_PATH + path, data=data,
                             **kwargs)

    def api_put(self, path, data={}, **kwargs):
        """Issue a PUT request to the API server

        :param path: The path that will be added to the API prefix
        :param data: The data to put to the url.
        """
        return self._request('put', API_PATH + path, data=data,
                             **kwargs)

    def api_delete(self, path, **kwargs):
        """Issue a delete to the API server.

        :param path: the path that will be added to the API prefix
        """
        return self._request('delete', API_PATH + path, **kwargs)

    def _request(self, method, path, **kwargs):
        """
        Send a request to the GoCardless API servers.

        :param method: the HTTP method to use (e.g. +:get+, +:post+)
        :param path: the path fragment of the URL
        """
        request_url = self.get_base_url() + path
        request = Request(method, request_url, params=kwargs.get("params"))
        logger.debug("Executing request to {0}".format(request_url))

        if 'auth' in kwargs:
            # If using HTTP basic auth, let requests handle it
            request.use_http_auth(*kwargs['auth'])
        else:
            # Default to using bearer auth with the access token
            request.use_bearer_auth(self._access_token)

        request.set_payload(kwargs.get('data'))
        response = request.perform()
        if type(response) == dict and "errors" in response.keys():
            raise ClientError("Error calling api, message was ",
                response["errors"])
        if type(response) == dict and "error" in response.keys():
            raise ClientError("Error calling api, message was ",
                response["error"])
        return response

    def merchant(self):
        """
        Returns the current Merchant's details.
        """
        merchant_url = '/merchants/%s' % self._merchant_id
        return Merchant(self.api_get(merchant_url), self)

    def user(self, id):
        """
        Find a user by id

        :param id: The users id
        """
        return User.find_with_client(id, self)

    def pre_authorization(self, id):
        """
        Find a pre authorization with id `id`

        :params id: The pre authorization id
        """
        return PreAuthorization.find_with_client(id, self)

    def subscription(self, id):
        """
        Returns a single subscription

        :param id: The subscription id, String
        """
        return Subscription.find_with_client(id, self)

    def bill(self, id):
        """
        Find a bill with id `id`
        """
        return Bill.find_with_client(id, self)

    def payout(self, id):
        """
        Find a payout with id `id`
        """
        return Payout.find_with_client(id, self)

    def create_bill(self, amount, pre_auth_id, name=None, description=None, currency=None):
        """Creates a new bill under an existing pre_authorization

        :param amount: The amount to bill
        :param pre_auth_id: The id of an existing pre_authorization which
          has not expire
        :param name: A name for this bill
        :param description: A description for this bill

        """
        return Bill.create_under_preauth(amount, pre_auth_id, self,
                                         name=name, description=description, currency=currency)

    def new_subscription_url(self, amount, interval_length, interval_unit,
                             name=None, description=None, interval_count=None,
                             start_at=None, expires_at=None, redirect_uri=None,
                             cancel_uri=None, state=None, user=None,
                             setup_fee=None, currency=None):
        """Generate a url for creating a new subscription

        :param amount: The amount to charge each time
        :param interval_length: The length of time between each charge, this
          is an integer, the units are specified by interval_unit.
        :param interval_unit: The unit to measure the interval length, must
          be one of "day", "week" or "month"
        :param name: The name to give the subscription
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
        :param user: A dictionary which will be used to prepopulate the sign
          up form the user sees, this can contain keys:

          - `first_name`
          - `last_name`
          - `email`

        :param setup_fee: A one off payment which will be taken at the start
          of the subscription.
        :param currency: 3 letter currency code for the payment to be taken in.
          Defaults to GBP.
        """
        params = urlbuilder.SubscriptionParams(
            amount, self._merchant_id,
            interval_length, interval_unit, name=name,
            description=description, interval_count=interval_count,
            expires_at=expires_at, start_at=start_at, user=user,
            setup_fee=setup_fee, currency=currency
        )
        builder = urlbuilder.UrlBuilder(self)
        return builder.build_and_sign(params, redirect_uri=redirect_uri,
                                      cancel_uri=cancel_uri, state=state)

    def new_bill_url(self, amount, name=None, description=None,
                     redirect_uri=None, cancel_uri=None, state=None,
                     user=None, currency=None):
        """Generate a url for creating a new bill

        :param amount: The amount to bill the customer
        :param name: The name of the bill
        :param description: The description of the bill
        :param redirect_uri: URI to redirect to after the authorization process
        :param cancel_uri: URI to redirect the user to if they cancel
          authorization
        :param state: String which will be passed to the merchant on
          redirect.
        :param user: A dictionary which will be used to prepopulate the sign
          up form the user sees, this can contain keys:

          - `first_name`
          - `last_name`
          - `email`

        :param currency: 3 letter currency code for the payment to be taken in.
          Defaults to GBP.
        """
        params = urlbuilder.BillParams(amount, self._merchant_id, name=name,
                                       description=description, user=user,
                                       currency=currency)
        builder = urlbuilder.UrlBuilder(self)
        return builder.build_and_sign(params, redirect_uri=redirect_uri,
                                      cancel_uri=cancel_uri, state=state)

    def new_preauthorization_url(self, max_amount, interval_length,
                                 interval_unit, expires_at=None, name=None,
                                 description=None, interval_count=None,
                                 calendar_intervals=None, redirect_uri=None,
                                 cancel_uri=None, state=None, user=None,
                                 setup_fee=None, currency=None):
        """Get a url for creating new pre_authorizations

        :param max_amount: A float which is the maximum amount for this
          pre_authorization
        :param interval_length: The length of this pre_authorization
        :param interval_unit: The units in which the interval_length
          is measured, must be one of
          - "day"
          - "week"
          - "month"
        :param expires_at: The date that this pre_authorization will
          expire, must be a datetime object which is in the future.
        :param name: A short string which is the name of the pre_authorization
        :param description: A longer string describing what the
          pre_authorization is for.
        :param interval_count: calculates expires_at based on the number of
          payment intervals you would like the resource to have. Must be a
          positive integer greater than 0. If you specify both an
          interval_count and an expires_at argument then the expires_at
          argument will take precedence.
        :param calendar_intervals: Describes whether the interval resource
          should be aligned with calendar weeks or months, default is False
        :param redirect_uri: URI to redirect to after the authorization process
        :param cancel_uri: URI to redirect the user to if they cancel
          authorization
        :param state: String which will be passed to the merchant on
          redirect.
        :param user: A dictionary which will be used to prepopulate the sign
          up form the user sees, this can contain keys:

          - `first_name`
          - `last_name`
          - `email`
        :param setup_fee: A one off payment which will be taken at the start
          of the subscription.
        :param currency: 3 letter currency code for the payment to be taken in.
          Defaults to GBP.
        """
        params = urlbuilder.PreAuthorizationParams(
            max_amount, self._merchant_id, interval_length, interval_unit,
            expires_at=expires_at, name=name, description=description,
            interval_count=interval_count, user=user,
            calendar_intervals=calendar_intervals, setup_fee=setup_fee,
            currency=currency
        )
        builder = urlbuilder.UrlBuilder(self)
        return builder.build_and_sign(params, redirect_uri=redirect_uri,
                                      cancel_uri=cancel_uri, state=state)

    # Create an alias to new_preauthorization_url to conform to the
    # documentation
    new_pre_authorization_url = new_preauthorization_url

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
        to_check = dict([[k, v] for k, v in six.iteritems(params) if k in keys])
        signature = generate_signature(to_check, self._app_secret)
        if not signature == params["signature"]:
            raise SignatureError("Invalid signature when confirming resource")
        auth_string = base64.b64encode(six.b("{0}:{1}".format(
            self._app_id, self._app_secret)))
        to_post = {
            "resource_id": params["resource_id"],
            "resource_type": params["resource_type"],
        }
        auth_details = (self._app_id, self._app_secret)
        return self.api_post("/confirm", to_post, auth=auth_details)

    def new_merchant_url(self, redirect_uri, state=None, merchant=None):
        """Get a URL for managing a new merchant

        This method creates a URL which partners should redirect
        merchants to in order to obtain permission to manage their GoCardless
        payments.

        :param redirect_uri: The URI where the merchant will be sent after
          authorizing.
        :param state: An optional string which will be present in the request
          to the redirect URI, useful for tracking the user.
        :param merchant: A dictionary which will be used to prepopulate the
          merchant sign up page, can contain any of the keys:

          - "name"
          - "phone_number"
          - "description"
          - "merchant_type" (either 'business', 'charity' or 'individual')
          - "company_name"
          - "company_registration"
          - "user" which can be a dictionary containing the keys:

            - "first_name"
            - "last_name"
            - "email"

        """
        params = {
            "client_id": self._app_id,
            "redirect_uri": redirect_uri,
            "scope": "manage_merchant",
            "response_type": "code",
        }
        if state:
            params["state"] = state
        if merchant:
            params["merchant"] = merchant
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
            "client_id": self._app_id,
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        query = to_query(params)
        url = "/oauth/access_token?{0}".format(query)
        # have to use _request so we don't add api_base to the url
        auth_details = (self._app_id, self._app_secret)
        result = self._request("post", url, auth=auth_details)
        self._access_token = result["access_token"]
        self._merchant_id = result["scope"].split(":")[1]
        return self._access_token

    def validate_webhook(self, params):
        """Check whether a webhook signature is valid

        Takes a dictionary of parameters, including the signature
        and returns a boolean indicating whether the signature is
        valid.

        :param params: A dictionary of data to validate, must include
          the key "signature"
        """
        return signature_valid(params, self._app_secret)

