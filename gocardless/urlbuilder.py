import base64
import datetime
import os
import urlparse
import utils

class UrlBuilder(object):

    def __init__(self, client):
        self.client = client

    def build_and_sign(self, params, state=None, redirect_uri=None, 
            cancel_uri=None):
        param_dict = {}
        param_dict[utils.singularize(params.resource_name)] = params.to_dict().copy()
        if state:
            param_dict["state"] = state
        if redirect_uri:
            param_dict["redirect_uri"] = redirect_uri
        if cancel_uri:
            param_dict["cancel_uri"] = cancel_uri
        param_dict["client_id"] = self.client._app_id        
        param_dict["timestamp"] = datetime.datetime.now().isoformat()[:-7] + "Z"
        param_dict["nonce"] = base64.b64encode(os.urandom(40))

        signature = utils.generate_signature(param_dict, self.client._app_secret)
        param_dict["signature"] = signature
        url = self.client.get_base_url() + "/connect/" + params.resource_name + \
                "/new?" + utils.to_query(param_dict)
        return url

class BasicParams(object):

    def __init__(self, amount, merchant_id, name=None, description=None):
        if not amount > 0:
            raise ValueError("amount must be positive, value passed was"
                    " {0}".format(amount))
        self.amount = amount
        self.merchant_id = merchant_id

        if name:
            self.name = name

        if description:
            self.description = description
        self.attrnames = ["amount", "name", "description", "merchant_id"]

    def to_dict(self):
        result = {}
        for attrname in self.attrnames:
            val = getattr(self, attrname, None)
            if val:
                result[attrname] = val
        return result


class PreAuthorizationParams(object):
    
    def __init__(self,max_amount, merchant_id, interval_length,\
            interval_unit, expires_at=None, name=None, description=None,\
            interval_count=None, calendar_intervals=None):

        self.merchant_id = merchant_id
        self.resource_name = "pre_authorizations"

        if not max_amount > 0:
            raise ValueError("""max_amount must be
                    positive value passed was {0}""".format(max_amount))
        self.max_amount = max_amount

        if not interval_length > 0:
            raise ValueError("interval_length must be positive, value "
                    "passed was {0}".format(interval_length))
        self.interval_length = interval_length

        valid_units = ["month", "day"]
        if interval_unit not in valid_units:
            raise ValueError("interval_unit must be one of {0},"
                    "value passed was {1}".format(valid_units, interval_unit))
        self.interval_unit = interval_unit

        if expires_at:
            if (expires_at - datetime.datetime.now()).total_seconds() < 0:
                raise ValueError("expires_at must be in the future, date "
                        "passed was {0}".format(expires_at.isoformat()))
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
        self.calendar_intervals = calendar_intervals if calendar_intervals\
                else None

    def to_dict(self):
        result = {}
        attrnames = ["merchant_id", "name", "description", \
                "interval_count", "interval_unit", "interval_length", \
                "max_amount", "calendar_intervals", "expires_at", \
                ]
        for attrname in attrnames:
            val = getattr(self, attrname, None)
            if val:
                result[attrname] = val
        return result


class BillParams(BasicParams):
    
    def __init__(self, amount, merchant_id, name=None, description=None):
        BasicParams.__init__(self, amount, merchant_id, name=name, description=description)
        self.resource_name  = "bills"



class SubscriptionParams(BasicParams):

    def __init__(self, amount, merchant_id, interval_length, interval_unit,
            name=None, description=None,start_at=None, expires_at=None, 
            interval_count=None):
        BasicParams.__init__(self, amount, merchant_id, description=description, name=name)
        self.resource_name = "subscriptions"
        self.merchant_id = merchant_id

        if not interval_length > 0:
            raise ValueError("interval_length must be positive, value "
                    "passed was {0}".format(interval_length))
        self.interval_length = interval_length

        valid_units = ["month", "day"]
        if interval_unit not in valid_units:
            raise ValueError("interval_unit must be one of {0},"
                    "value passed was {1}".format(valid_units, interval_unit))
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
        
        self.attrnames.extend(["description", "interval_count",
                "interval_unit", "interval_length", "expires_at",
                "start_at"])

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



