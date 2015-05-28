import datetime
import mock
import unittest

import six
from six.moves import urllib

import gocardless
from gocardless import utils, urlbuilder

class ExpiringLimitTestCase(object):
    """superclass factoring out tests for expiring limit param objects"""

    def test_interval_length_is_positive(self):
        pars = self.create_params(10, "1321230", 1, "day")
        with self.assertRaises(ValueError):
            pars = self.create_params(10, "1123210", -1, "day")

    def test_interval_unit_is_valid(self):
        for interval_unit in ["day", "week", "month"]:
            pars = self.create_params(10, 10, "11235432", interval_unit)
        with self.assertRaises(ValueError):
            pars = self.create_params(10, 10, "1432233123", "invalid")

    def _future_date_tester(self, argname):
        invalid_date = datetime.datetime.now() - datetime.timedelta(100)
        valid_date = datetime.datetime.now() + datetime.timedelta(2000)
        par1 = self.create_params(10, 10, "23423421", "day", **{argname:valid_date})
        with self.assertRaises(ValueError):
            par1 = self.create_params(10, 10, "2342341", "day",
                    **{argname:invalid_date})

    def test_expires_at_in_future(self):
        self._future_date_tester("expires_at")

    def test_interval_count_positive(self):
        with self.assertRaises(ValueError):
            self.create_params(10, 10, "merchid", "day", interval_count=-1)

class PreAuthParamsTestCase(ExpiringLimitTestCase, unittest.TestCase):

    def default_args_construct(self, extra_options):
        """
        For testing optional arguments, builds the param object with valid
        required arguments and adds optionl arguments as keywords from
        `extra_options`

        :param extra_options: Extra optional keyword arguments to pass to
        the constructor.
        """
        return urlbuilder.\
                PreAuthorizationParams(12, "3456", 6, "month", **extra_options)

    def create_params(self, *args, **kwargs):
        return urlbuilder.PreAuthorizationParams(*args, **kwargs)

    def test_max_amount_is_positive(self):
        self.assertRaises(ValueError, \
                urlbuilder.PreAuthorizationParams, -1, "1232532", 4, "month")

    def test_interval_length_is_a_positive_integer(self):
        self.assertRaises(ValueError, \
                urlbuilder.PreAuthorizationParams, 12, "!2343", -3, "month")

    def test_interval_unit_is_one_of_accepted(self):
        for unit_type in ["month", "day", "week"]:
            pa = urlbuilder.PreAuthorizationParams(12, "1234", 3, unit_type)
        self.assertRaises(ValueError, \
                urlbuilder.PreAuthorizationParams, 21,"1234", 4, "soem other unit")

    def test_expires_at_is_later_than_now(self):
        earlier = datetime.datetime.now() - datetime.timedelta(1)
        self.assertRaises(ValueError, self.default_args_construct, \
                {"expires_at":earlier})

    def test_interval_count_is_postive_integer(self):
        self.assertRaises(ValueError, self.default_args_construct, \
                {"interval_count":-1})


class PreAuthParamsToDictTestCase(unittest.TestCase):
    def setUp(self):
        self.all_params = {
                "max_amount":12,
                "interval_unit":"day",
                "interval_length":10,
                "merchant_id":"1234435",
                "name":"aname",
                "description":"adesc",
                "interval_count":123,
                "currency":"GBP",
                "expires_at":datetime.datetime.strptime("2020-01-01", "%Y-%m-%d"),
                "calendar_intervals":True
                }
        self.required_keys = [
                "max_amount", "interval_unit", "interval_length", "merchant_id"]

    def create_from_params_dict(self, in_params):
        params = in_params.copy()
        pa = urlbuilder.PreAuthorizationParams(params.pop("max_amount"), \
                params.pop("merchant_id"), \
                params.pop("interval_length"), \
                params.pop("interval_unit"),\
                **params)
        return pa

    def assert_inverse(self, keys):
        params = dict([[k,v] for k,v in six.iteritems(self.all_params) \
                if k in keys])
        pa = self.create_from_params_dict(params)
        self.assertEqual(params, pa.to_dict())

    def test_to_dict_all_params(self):
        self.assert_inverse(list(self.all_params.keys()))

    def test_to_dict_only_required(self):
        self.assert_inverse(self.required_keys)


class BillParamsTestCase(unittest.TestCase):

    def create_params(self, *args, **kwargs):
        return urlbuilder.BillParams(*args, **kwargs)

    def test_amount_is_positive(self):
        params = self.create_params(10, "merchid")
        with self.assertRaises(ValueError):
            par2 = self.create_params(-1, "merchid")

    def test_to_dict_required(self):
        pars = self.create_params(10, "merchid")
        res = pars.to_dict()
        expected = {"amount":10, "merchant_id":"merchid"}
        self.assertEqual(res, expected)

    def test_to_dict_optional(self):
        pars = self.create_params(10, "merchid", name="aname", description="adesc")
        res = pars.to_dict()
        expected = {"amount":10,
                "name":"aname",
                "description":"adesc",
                "merchant_id":"merchid"
                }
        self.assertEqual(res, expected)

    def test_resource_name_is_bills(self):
        pars = urlbuilder.BillParams(10, "merchid")
        self.assertEqual(pars.resource_name, "bills")


class SubscriptionParamsTestCase(ExpiringLimitTestCase, unittest.TestCase):

    def create_params(self, *args, **kwargs):
        return urlbuilder.SubscriptionParams(*args, **kwargs)

    def test_setup_fee(self):
        pars = self.create_params(10, "merchid", 10, "day", setup_fee=20)
        expected = {
                "merchant_id": "merchid",
                "amount": 10,
                "interval_length": 10,
                "interval_unit" : "day",
                "setup_fee": 20
                }
        self.assertEqual(expected, pars.to_dict())

    def test_start_at_in_future(self):
        valid_date = datetime.datetime.now() + datetime.timedelta(200)
        invalid_date = datetime.datetime.now() - datetime.timedelta(100)
        par1 = self.create_params(10,"merchid", 10, "day", start_at=valid_date)
        with self.assertRaises(ValueError):
            par2 = self.create_params(10, "merchid", 10, "day",
                    start_at=invalid_date)

    def test_expires_at_after_start_at(self):
        date1 = datetime.datetime.now() + datetime.timedelta(100)
        date2 = datetime.datetime.now() + datetime.timedelta(200)
        par1 = self.create_params(10, "merchid", 10, "day",
                expires_at=date2, start_at=date1)
        with self.assertRaises(ValueError):
            par2 = self.create_params(10, "merchid", 10, "day",
                    expires_at=date1, start_at=date2)

    def test_to_dict_only_required(self):
        expected = {
                "merchant_id":"merchid",
                "amount":10,
                "interval_length":10,
                "interval_unit":"day"}
        pars = self.create_params(10, "merchid", 10, "day")
        self.assertEqual(expected, pars.to_dict())

    def test_to_dict_all(self):
        start_at = datetime.datetime.now() + datetime.timedelta(1000)
        expires_at =datetime.datetime.now() + datetime.timedelta(2000)
        expected = {
                "merchant_id":"merchid",
                "amount":10,
                "interval_length":10,
                "interval_unit":"day",
                "interval_count":5,
                "start_at":start_at.isoformat()[:-7] + "Z",
                "expires_at":expires_at.isoformat()[:-7] + "Z",
                "name":"aname",
                "description":"adesc",
                }
        par = self.create_params(10, "merchid", 10, "day", start_at=start_at,
                expires_at=expires_at, interval_count=5, name="aname",
                description="adesc")
        self.assertEqual(expected, par.to_dict())


class PrepopDataTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_prepop = {"first_name": "Tom",
                "last_name": "Blomfield",
                "email": "tom@gocardless.com"
                }

    def assert_prepop(self, params):
        self.assertEqual(params.to_dict()["user"], self.mock_prepop)

    def test_bill_params(self):
        params = urlbuilder.BillParams(10, "amerchid", user=self.mock_prepop)
        self.assert_prepop(params)

    def test_sub_params(self):
        params = urlbuilder.SubscriptionParams(10, "merchid", 3, "day", user=self.mock_prepop)
        self.assert_prepop(params)

    def test_pre_auth_params(self):
        params = urlbuilder.PreAuthorizationParams(10, "amerchid", 5, "day", user=self.mock_prepop)
        self.assert_prepop(params)



