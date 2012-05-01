.. image:: https://gocardless.com/resources/logo.png

The GoCardless Python Client Library
====================================

This module provides a wrapper around the GoCardless payments API, the
interface to the api is provided by the `gocardless.Client` object. See the
documentation for that class for how to obtain a reference.

By default the library will attempt to use the GoCardless production
environment, for testing purposes this is not what you want and you should set
the `gocardless.environment` to "sandbox".

Once you have obtained an instance of a client you can use that client to
generate urls for receiving payments. You can also use it to query the api for
information about payments resources using an active resource style API. For
example, to get all of a merchants bills::

    >>> merchant = client.merchant()
    >>> merchant.bills()
    >>> [<gocardless.resources.Bill at 0x29a6050>]

