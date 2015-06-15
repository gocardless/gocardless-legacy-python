
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

VERSION = (0, 5, 2)

def get_version():
    return '.'.join(str(part) for part in VERSION)

from .client import Client

#import as clientlib so that we don't shadow with the client variable
from . import client as clientlib
from gocardless.resources import (Bill, Subscription, PreAuthorization, User,
                                  Merchant)

environment = 'production'
"""The environment GoCardless executes API requests against, should be
either "production" or "sandbox"
"""

client = None
"""The client for merchants to use. Does not exist until
:py:func:`gocardless.set_details` has been called.
"""


def set_details(app_id=None, app_secret=None, access_token=None,
                merchant_id=None):
    """Set the global account details to use for requests

    The parameters are your security details which can be found
    on your gocardless developer details page. All are mandatory
    """
    if app_id is None:
        raise ValueError("app_id is required")
    if app_secret is None:
        raise ValueError("app_secret is required")
    if access_token is None:
        raise ValueError("access_token is required")
    if merchant_id is None:
        raise ValueError("merchant_id is required")

    global client
    client = Client(app_id, app_secret, access_token=access_token,
                    merchant_id=merchant_id)

