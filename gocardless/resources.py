import datetime
import re
import sys

from . import utils
import gocardless
from gocardless.exceptions import ClientError

import six


class ResourceMetaClass(type):

    def __new__(meta, name, bases, attrs):
        #resoures inherit date fields from superclasses
        for base in bases:
            if hasattr(base, "date_fields") and "date_fields" in attrs:
                attrs["date_fields"].extend(base.date_fields)
        return type.__new__(meta, name, bases, attrs)


@six.add_metaclass(ResourceMetaClass)
class Resource(object):
    """A GoCardless resource

    Subclasses of `Resource` define class attributes to specify how
    the resource is fetched and represented.

    The class attribute `endpoint` is the path to the resource on the server.

    The class attribute `date_fields` names fields which will be converted
    into `datetime.datetime` objects on construction.

    The class attribute `reference_fields` names fields which are uris to other
    resources and will be converted into functions which can be called to
    retrieve those resources.
    """

    date_fields = ["created_at"]
    reference_fields = []

    def __init__(self, in_attrs, client):
        """Construct a resource

        :param in_attrs: A dictionary of attributes, usually obtained from a
        JSON response.
        :param client: an instance of gocardless.Client
        """
        attrs = in_attrs.copy()
        self._raw_attrs = attrs.copy()
        self.id = attrs["id"]
        self.client = client
        if "sub_resource_uris" in attrs:
            #For each subresource_uri create a method which grabs data
            #from the URI and uses it to instantiate the relevant class
            #and return it.
            for name, uri in six.iteritems(attrs.pop("sub_resource_uris")):
                path = re.sub(".*/api/v1", "", uri)
                sub_klass = self._get_klass_from_name(name)
                def create_get_resource_func(the_path, the_klass):
                    # In python functions close over their environment so in
                    # order to create the correct closure we need a function
                    # creator, see
                    # http://stackoverflow.com/questions/233673/
                    #         lexical-closures-in-python/235764#235764
                    def get_resources(inst, **params):
                        data = inst.client.api_get(the_path, params=params)
                        return [the_klass(attrs, self.client) for attrs in data]
                    return get_resources
                res_func = create_get_resource_func(path, sub_klass)
                func_name = "{0}".format(name)
                res_func.name = func_name
                setattr(self, func_name,
                        six.create_bound_method(res_func, self))

        for fieldname in self.date_fields:
            val = attrs.pop(fieldname)
            if val is not None:
                setattr(self, fieldname,
                        datetime.datetime.strptime(val, "%Y-%m-%dT%H:%M:%SZ"))
            else:
                setattr(self, fieldname, None)

        for fieldname in self.reference_fields:
            id = attrs.pop(fieldname)
            def create_get_func(the_klass, the_id):
                def get_referenced_resource(inst):
                    return the_klass.find_with_client(the_id, self.client)
                return get_referenced_resource
            name = fieldname.replace("_id", "")
            klass = self._get_klass_from_name(name)
            func = create_get_func(klass, id)
            setattr(self, name, six.create_bound_method(func, self))

        for key, value in six.iteritems(attrs):
            setattr(self, key, value)

    def _get_klass_from_name(self, name):
        module = sys.modules[self.__module__]
        klass = getattr(module, utils.singularize(utils.camelize(name)))
        return klass

    def get_endpoint(self):
        return self.endpoint.replace(":id", self.id)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._raw_attrs == other._raw_attrs
        return False

    def __hash__(self):
        return hash(self._raw_attrs["id"])

    @classmethod
    def find_with_client(cls, id, client):
        path = cls.endpoint.replace(":id", id)
        return cls(client.api_get(path), client)

    @classmethod
    def find(cls, id):
        if not gocardless.client:
            raise ClientError("You must set your account details first")
        return cls.find_with_client(id, gocardless.client)


class Merchant(Resource):
    endpoint = "/merchants/:id"
    date_fields = ["next_payout_date"]


class Subscription(Resource):
    endpoint = "/subscriptions/:id"
    reference_fields = ["user_id", "merchant_id"]
    date_fields = ["expires_at", "next_interval_start"]

    def cancel(self):
        path = "{0}/cancel".format(self.endpoint.replace(":id", self.id))
        self.client.api_put(path)


class PreAuthorization(Resource):
    endpoint = "/pre_authorizations/:id"
    date_fields = ["expires_at", "next_interval_start"]
    reference_fields = ["user_id", "merchant_id"]

    def create_bill(self, amount, name=None, description=None,
                    charge_customer_at=None, currency=None):
        return Bill.create_under_preauth(amount, self.id, self.client,
                                         name=name, description=description,
                                         charge_customer_at=charge_customer_at,
                                         currency=currency)

    def cancel(self):
        path = "{0}/cancel".format(self.endpoint.replace(":id", self.id))
        self.client.api_put(path)


class Bill(Resource):
    endpoint = "/bills/:id"
    date_fields = ["paid_at"]
    reference_fields = ["merchant_id", "user_id", "payout_id"]

    @classmethod
    def create_under_preauth(self, amount, pre_auth_id, client, name=None,
                             description=None, charge_customer_at=None, currency=None):
        path = "/bills"
        params = {
            "bill": {
                "amount": amount,
                "pre_authorization_id": pre_auth_id
            }
        }
        if name:
            params["bill"]["name"] = name
        if description:
            params["bill"]["description"] = description
        if charge_customer_at:
            params["bill"]["charge_customer_at"] = charge_customer_at
        if currency:
            params["bill"]["currency"] = currency
        return Bill(client.api_post(path, params), client)

    def retry(self):
        path = "{0}/retry".format(self.endpoint.replace(":id", self.id))
        self.client.api_post(path)

    def cancel(self):
        path = "{0}/cancel".format(self.endpoint.replace(":id", self.id))
        self.client.api_put(path)

    """Please note the refund endpoint is disabled by default

    If you have over 50 successful payments on your account and you
    require access to the refund endpoint, please email help@gocardless.com
    """
    def refund(self):
        path = "{0}/refund".format(self.endpoint.replace(":id", self.id))
        self.client.api_post(path)

class Payout(Resource):
    endpoint = "/payouts/:id"
    date_fields = ["paid_at"]

class User(Resource):
    endpoint = "/users/:id"
