import datetime
import json
import logging
import re
import sys
import types

import utils
import gocardless
from gocardless.exceptions import ClientError


class Resource(object):

    def __init__(self, attrs, client):
        self.id = attrs["id"]
        self.client = client
        if "sub_resource_uris" in attrs:
            for name, uri in attrs.pop("sub_resource_uris").items():
                path = re.sub(".*/api/v1", "", uri)
                module = sys.modules[self.__module__]
                sub_klass = getattr(module, utils.singularize(utils.camelize(name)))
                def create_get_resource_func(the_path, the_klass):
                    """
                    In python functions close over their environment so in
                    order to create the correct closure we need a function
                    creator, see 
                    http://stackoverflow.com/questions/233673/\
                            lexical-closures-in-python/235764#235764
                    """
                    def get_resources(inst):
                        data = inst.client.api_get(the_path)
                        return [the_klass(attrs, self.client) for attrs in data]
                    return get_resources
                res_func = create_get_resource_func(path, sub_klass)
                func_name = "get_{0}".format(name)
                res_func.name = func_name
                setattr(self, func_name, types.MethodType(res_func, self, self.__class__))
        self.created_at = datetime.datetime.strptime(attrs.pop("created_at"), "%Y-%m-%dT%H:%M:%SZ")
        for key, value in attrs.items():
            setattr(self, key, value)

    def get_endpoint(self):
        return self.endpoint.replace(":id", self.id)

    @classmethod
    def find_with_client(cls, id, client):
        path = cls.endpoint.replace(":id", id)
        return cls(client.api_get(path), client)

    @classmethod
    def find(cls, id):
        if not gocardless.global_client:
            raise ClientError("You must set your account details first")
        return cls.find_with_client(id, gocardless.global_client)



class Merchant(Resource):
    endpoint = "/merchants/:id"

class Subscription(Resource):
    endpoint = "/subscriptions/:id"

class PreAuthorization(Resource):
    endpoint = "/pre_authorizations/:id"

class Bill(Resource):
    endpoint = "/bills/:id"

class User(Resource):
    endpoint = "/users/:id"

    
