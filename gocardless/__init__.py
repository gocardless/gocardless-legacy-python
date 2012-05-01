
"""The GoCardless Python Client Library

This module provides a wrapper around the GoCardless payments API, the
interface to the api is provided by the :py:class:`gocardless.Client`
object. See the documentation for that class for how to obtain a reference.

By default the library will attempt to use the GoCardless production
environment, for testing purposes this is not what you want and you
should set the :py:data:`gocardless.environment` to "sandbox".

Once you have obtained an instance of a client you can use that client
to generate urls for receiving payments. You can also use it to query
the api for information about payments resources using an active resource
style API. For example, to get all of a merchants bills:

.. code-block:: python

    >>> merchant = client.merchant()
    >>> merchant.bills()
    >>> [<gocardless.resources.Bill at 0x29a6050>]
"""

VERSION = (0, 1, 0)

def get_version():
    return '.'.join(str(part) for part in VERSION)

from .client import Client

#import as clientlib so that we don't shadow with the client variable
import client as clientlib
from gocardless.resources import Bill, Subscription, PreAuthorization, User, Merchant

environment = 'production'
"""The environment GoCardless executes API requests against, should be
either "production" or "sandbox"
"""

client = None
"""The client for merchants to use. Does not exist until
:py:func:`gocardless.set_details` has been called.
"""

def set_details(details):
    """Set the global account details to use for requests

    Should be a dictionary with the following keys
      - "app_id"
      - "app_secret"
      - "token"
      - "merchant_id"
    """
    global client
    client = Client(details["app_id"],
            details["app_secret"],
            access_token=details["token"],
            merchant_id=details["merchant_id"])

