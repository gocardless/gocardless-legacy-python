.. image:: https://s3-eu-west-1.amazonaws.com/gocardless/images/client-lib-headers/python-lib-header.png
  :target: https://gocardless.com/docs?language=python

[![Build Status](https://secure.travis-ci.org/gocardless/gocardless-python.png?branch=master)](http://travis-ci.org/gocardless/gocardless-python)

This module provides a wrapper around the GoCardless payments API, the
interface to the api is provided by the `gocardless.Client` object. See the
documentation for that class for how to obtain an instance.

By default the library will attempt to use the GoCardless production
environment, for testing purposes this is not what you want and you should set
the `gocardless.environment` to "sandbox".::

    >>> gocardless.environment = "sandbox"

Set your account details:::
    
    >>> gocardless.set_details(app_id="kzCOPw2JtJvRQxKOPEREQTGvxLvkoMS1Eb0Dgl5QVc1W0NKpOEZDvESfGOI_kkG2l",
    >>>     app_secret="IO9AlgPsbYNCtFlcOFGROBrGB3Mi07PFYSn2zx4uK5xaWJI1AzwnYeC86x46ji_g",
    >>>     access_token="5EFkzOrUOZ8t+iaP86NggIy+FOFSD0f7QMnMd+Q3P4mQk17Kzq9G1vYrNlEWFldlg",
    >>>     merchant_id="02FX1YFDAS")

You can now use the `gocardless.client` object to generate urls for receiving payments.::

    >>> gocardless.client.new_bill_url(10)

Users who click on this link will be taken to the GoCardless website to make a payment to 
your account.

You can also use it to query the api for information about payments resources using an 
active resource style API. For example, to get all of a merchants bills::

    >>> merchant = client.merchant()
    >>> merchant.bills()
    >>> [<gocardless.resources.Bill at 0x29a6050>]

Contribute
==========

Fork the repo then clone it to your machine and install in "develop" mode
(preferably using a virtualenv)::

    mkvirtualenv gocardless
    git clone https://github.com/<username>/gocardless-python
    cd gocardless-python
    python setup.py develop

Install the testing dependencies::

    pip install -r requirements.txt

and run the test suite::

    nosetests
