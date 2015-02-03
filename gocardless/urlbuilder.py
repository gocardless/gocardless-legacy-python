import base64
import datetime
import os
from . import utils


class UrlBuilder(object):
    """Handles correctly encoding and signing api urls"""

    def __init__(self, client):
        """Create a new UrlBuilder

        :param client: an instance of `gocardless.Client` which will
        be used to sign urls.
        """
        self.client = client

    def build_and_sign(self, params, state=None, redirect_uri=None,
                       cancel_uri=None):
        """Builds a url and returns it as a string

        :param params: A Params class corresponding to the resource for which
        you wish to create a url. For example, to create a Subscription url
        pass an instance of SubscriptionParams.
        :param state: The state argument to be encoded in the query string.
        :param redirect_uri: The redirect uri the user will be sent to after
        the resource has been created.
        :param cancel_uri: The uri the user will be redirected to if they
        cancel the resource creation
        """
        param_dict = {}
        resource_name = utils.singularize(params.resource_name)
        param_dict[resource_name] = params.to_dict().copy()
        if state:
            param_dict["state"] = state
        if redirect_uri:
            param_dict["redirect_uri"] = redirect_uri
        if cancel_uri:
            param_dict["cancel_uri"] = cancel_uri
        param_dict["client_id"] = self.client._app_id
        iso_time = datetime.datetime.utcnow().isoformat()
        param_dict["timestamp"] = iso_time[:-7] + "Z"
        param_dict["nonce"] = base64.b64encode(os.urandom(40))

        signature = utils.generate_signature(param_dict, self.client._app_secret)
        param_dict["signature"] = signature
        url = "{0}/connect/{1}/new?{2}".format(
            self.client.get_base_url(),
            params.resource_name,
            utils.to_query(param_dict),
        )
        return url


class BasicParams(object):

    def __init__(self, amount, merchant_id, name=None, description=None,
                 user=None, currency=None):
        if not amount > 0:
            raise ValueError("amount must be positive, value passed was"
                             " {0}".format(amount))
        self.amount = amount
        self.merchant_id = merchant_id

        if name:
            self.name = name

        if user:
            self.user = user

        if description:
            self.description = description

        if currency:
            self.currency = currency
        self.attrnames = [
            "amount", "name", "description", "merchant_id", "user", "currency"
        ]

    def to_dict(self):
        result = {}
        for attrname in self.attrnames:
            val = getattr(self, attrname, None)
            if val:
                result[attrname] = val
        return result


class PreAuthorizationParams(object):

    def __init__(self, max_amount, merchant_id, interval_length,
                 interval_unit, expires_at=None, name=None, description=None,
                 interval_count=None, calendar_intervals=None, user=None,
                 setup_fee=None, currency=None):

        self.merchant_id = merchant_id
        self.resource_name = "pre_authorizations"

        if user:
            self.user = user

        if not max_amount > 0:
            raise ValueError("""max_amount must be
                    positive value passed was {0}""".format(max_amount))
        self.max_amount = max_amount

        self.setup_fee = setup_fee

        interval_length = int(interval_length)
        if not interval_length > 0:
            raise ValueError("interval_length must be positive, value "
                             "passed was {0}".format(interval_length))
        self.interval_length = interval_length

        valid_units = ["month", "day", "week"]
        if interval_unit not in valid_units:
            message = "interval_unit must be one of {0}, value passed was {1}"
            raise ValueError(message.format(valid_units, interval_unit))
        self.interval_unit = interval_unit

        if expires_at:
            if (expires_at - datetime.datetime.now()).total_seconds() < 0:
                time_str = expires_at.isoformat()
                raise ValueError("expires_at must be in the future, date "
                                 "passed was {0}".format(time_str))
            self.expires_at = expires_at
        else:
            self.expires_at = None

        if interval_count:
            if interval_count < 0:
                raise ValueError("interval_count must be positive "
                                 "value passed was {0}".format(interval_count))
            self.interval_count = interval_count
        else:
            self.interval_count = None

        self.name = name if name else None
        self.description = description if description else None
        self.calendar_intervals = None
        if calendar_intervals:
            self.calendar_intervals = calendar_intervals
        self.currency = currency if currency else None

    def to_dict(self):
        result = {}
        attrnames = [
            "merchant_id", "name", "description", "interval_count",
            "interval_unit", "interval_length", "max_amount",
            "calendar_intervals", "expires_at", "user", "setup_fee",
            "currency"
        ]
        for attrname in attrnames:
            val = getattr(self, attrname, None)
            if val:
                result[attrname] = val
        return result


class BillParams(BasicParams):

    def __init__(self, amount, merchant_id, name=None, description=None,
                 user=None, currency=None):
        BasicParams.__init__(self, amount, merchant_id, name=name,
                             user=user, description=description,
                             currency=currency)
        self.resource_name = "bills"


class SubscriptionParams(BasicParams):

    def __init__(self, amount, merchant_id, interval_length, interval_unit,
                 name=None, description=None, start_at=None, expires_at=None,
                 interval_count=None, user=None, setup_fee=None,
                 currency=None):
        BasicParams.__init__(self, amount, merchant_id, user=user,
                             description=description, name=name)
        self.resource_name = "subscriptions"
        self.merchant_id = merchant_id

        interval_length = int(interval_length)
        if not interval_length > 0:
            raise ValueError("interval_length must be positive, value "
                             "passed was {0}".format(interval_length))
        self.interval_length = interval_length

        valid_units = ["month", "day", "week"]
        if interval_unit not in valid_units:
            message = "interval_unit must be one of {0}, value passed was {1}"
            raise ValueError(message.format(valid_units, interval_unit))
        self.interval_unit = interval_unit

        if expires_at:
            self.check_date_in_future(expires_at, "expires_at")
            self.expires_at = expires_at

        if start_at:
            self.check_date_in_future(start_at, "start_at")
            self.start_at = start_at

        if expires_at and start_at:
            if (expires_at - start_at).total_seconds() < 0:
                raise ValueError("start_at must be before expires_at")

        if interval_count:
            if interval_count < 0:
                raise ValueError("interval_count must be positive "
                                 "value passed was {0}".format(interval_count))
            self.interval_count = interval_count

        self.name = name if name else None
        self.description = description if description else None
        self.setup_fee = setup_fee
        self.currency = currency if currency else None

        self.attrnames.extend([
            "description", "interval_count", "interval_unit",
            "interval_length", "expires_at", "start_at", "setup_fee",
            "currency"
        ])

    def check_date_in_future(self, date, argname):
        if (date - datetime.datetime.now()).total_seconds() < 0:
            raise ValueError("{0} must be in the future, date passed was"
                             "{1}".format(argname, date.isoformat()))

    def to_dict(self):
        result = {}
        for attrname in self.attrnames:
            val = getattr(self, attrname, None)
            if val:
                if attrname in ["start_at", "expires_at"]:
                    result[attrname] = val.isoformat()[:-7] + "Z"
                else:
                    result[attrname] = val
        return result

