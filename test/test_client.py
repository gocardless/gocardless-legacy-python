import base64
import datetime
import json
import unittest
import mock
from mock import patch
import os
import sys
import time

import six
from six.moves import urllib

from . import fixtures
import gocardless
import gocardless.client
from gocardless.client import Client
from gocardless import utils, urlbuilder, resources
from gocardless.exceptions import SignatureError, ClientError
from .test_resources import create_mock_attrs

mock_account_details = {
    'app_id': 'id01',
    'app_secret': 'sec01',
    'token': 'tok01',
    'merchant_id': fixtures.merchant_json["id"],
}


def create_mock_client(details):
    return Client(details["app_id"],
            details["app_secret"],
            access_token=details["token"],
            merchant_id=details["merchant_id"])


def get_url_params(url):
    param_dict = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    return dict([[k,v[0]] for k,v in six.iteritems(param_dict)])


class ClientTestCase(unittest.TestCase):

    def setUp(self):
        self.account_details = mock_account_details.copy()
        self.client = create_mock_client(self.account_details)

    def test_error_raises_clienterror_string(self):
        with patch('gocardless.clientlib.Request') as mock_request_module:
            #Test with response containing "error" as a string
            mock_request = mock.Mock()
            mock_request.perform.return_value = {"error":"anerrormessage"}
            mock_request_module.return_value = mock_request
            with self.assertRaises(ClientError) as ex:
                self.client.api_get("/somepath")
                self.assertEqual(six.text_type(ex), "Error calling api, message"
                    " was anerrormessage")

    def test_error_raises_clienterror_list(self):
        with patch('gocardless.clientlib.Request') as mock_request_module:
            #Test with response containing "error" as a list
            mock_request = mock.Mock()
            mock_request.perform.return_value = {"error":["Server Error", "Oops"]}
            mock_request_module.return_value = mock_request
            with self.assertRaises(ClientError) as ex:
                self.client.api_get("/somepath")
            # Because dicts don't guarantee a key order
            messages = [s.strip() for s in ex.exception.message[31:].split(',')]
            messages.sort()
            self.assertEqual(messages, ['Oops', 'Server Error'])

    def test_errors_raises_clienterror(self):
        with patch('gocardless.clientlib.Request') as mock_request_module:
            #Test with response containing "errors" with a dict
            mock_request = mock.Mock()
            mock_request.perform.return_value = {"errors":{"name":["too short"], "email":["taken","invalid"]}}
            mock_request_module.return_value = mock_request
            with self.assertRaises(ClientError) as ex:
                self.client.api_get("/somepath")
            # Because dicts don't guarantee a key order
            messages = [s.strip() for s in ex.exception.message[31:].split(',')]
            messages.sort()
            self.assertEqual(messages, ['email invalid', 'email taken', 'name too short'])

    def test_error_when_result_is_list(self):
        #Test for an issue where the code which checked if
        #the response was an error failed because it did
        #not first check if the response was a dictionary.
        with patch('gocardless.clientlib.Request') as mock_req_mod:
            mock_request = mock.Mock()
            mock_request.perform.return_value = ["one", "two"]
            mock_req_mod.return_value = mock_request
            self.client.api_get("/somepath")


    def test_base_url_returns_the_correct_url_for_production(self):
        gocardless.environment = 'production'
        self.assertEqual(Client.get_base_url(), 'https://gocardless.com')

    def test_base_url_returns_the_correct_url_for_sandbox(self):
        gocardless.environment = 'sandbox'
        self.assertEqual(Client.get_base_url(), 'https://sandbox.gocardless.com')
        gocardless.environment = "production"

    def test_base_url_returns_the_correct_url_when_set_manually(self):
        old_url = Client.base_url
        Client.base_url = 'https://abc.gocardless.com'
        self.assertEqual(Client.get_base_url(), 'https://abc.gocardless.com')
        Client.base_url = old_url

    def test_get_merchant(self):
        with patch.object(self.client, 'api_get'):
            self.client.api_get.return_value = fixtures.merchant_json
            merchant = self.client.merchant()
            self.assertEqual(merchant.id, self.account_details["merchant_id"])

    def test_get_subscription(self):
        self._get_resource_tester("subscription", fixtures.subscription_json)

    def test_get_user(self):
        self._get_resource_tester("user", create_mock_attrs({}))

    def test_get_pre_authorization(self):
        mock_date = datetime.datetime.now().isoformat()[:-7] + "Z"
        mock_attrs = {
                "user_id":"123456",
                "expires_at":mock_date,
                "next_interval_start":mock_date
                }
        self._get_resource_tester("pre_authorization",
                create_mock_attrs(mock_attrs))

    def test_get_bill(self):
        self._get_resource_tester("bill", create_mock_attrs(
                {"paid_at":datetime.datetime.now().isoformat()[:-7] + "Z",
                "user_id":"someuserid", "payout_id": "XXX"}))

    def _get_resource_tester(self, resource_name, resource_fixture):
        expected_klass = getattr(sys.modules["gocardless.resources"], utils.camelize(resource_name))
        with patch.object(self.client, 'api_get'):
            self.client.api_get.return_value = resource_fixture
            obj = getattr(self.client, resource_name)("1")
            self.assertEqual(resource_fixture["id"], obj.id)
            self.assertIsInstance(obj, expected_klass)

    def test_set_details_creates_client(self):
        gocardless.set_details(app_id=mock_account_details["app_id"],
                app_secret=mock_account_details["app_secret"],
                access_token=mock_account_details["token"],
                merchant_id=mock_account_details["merchant_id"])
        self.assertIsNotNone(gocardless.client)

    def test_set_details_valueerror_raised_when_details_not_present(self):
        details = mock_account_details.copy()
        details["access_token"] = details["token"]
        details.pop("token")
        for key in details.keys():
            #make sure that every key is required by passing in a hash with
            #all but one key missing
            invalid_details = details.copy()
            invalid_details.pop(key)
            with self.assertRaises(ValueError):
                gocardless.set_details(**invalid_details)

    def test_create_bill(self):
        with patch.object(self.client, 'api_post') as mock_post:
            expected_path = "/bills"
            expected_params = {
                    "amount":10,
                    "pre_authorization_id": "someid"
                    }
            mock_bill = resources.Bill(fixtures.bill_json.copy(), self.client)
            mock_post.return_value = fixtures.bill_json
            res = self.client.create_bill(10, "someid")
            mock_post.assert_called_with("/bills",
                    {"bill":expected_params})
            self.assertEqual(res, mock_bill)

    @patch('gocardless.clientlib.Request')
    def test_request_with_auth(self, mock_reqclass):
        mock_request = mock.Mock()
        mock_request.perform.return_value = ["someval"]
        mock_reqclass.return_value = mock_request
        self.client._request("post", "somepath", auth=("username", "password"))
        mock_request.use_http_auth.assert_called_with("username", "password")

class ConfirmResourceTestCase(unittest.TestCase):

    def setUp(self):
        self.client = create_mock_client(mock_account_details)
        self.resource_path = "/somepath/morepath"
        self.params =  {
                "resource_uri":"http://aresource.com/api/v1{0}".format(
                    self.resource_path),
                "resource_id":"1",
                "resource_type":"subscription",
                }

    def test_incorrect_signature_raises(self):
        self.params["signature"] =  "asignature"
        with self.assertRaises(SignatureError):
            self.client.confirm_resource(self.params)

    def test_resource_posts(self):
        self.params["signature"] = utils.generate_signature(self.params,
                mock_account_details["app_secret"])
        with patch.object(self.client, 'api_post') as mock_post:
            expected_data = {
                    "resource_type":self.params["resource_type"],
                    "resource_id":self.params["resource_id"]
                    }
            expected_auth = (mock_account_details["app_id"],
                mock_account_details["app_secret"])
            self.client.confirm_resource(self.params)
            expected_path = "/confirm"
            mock_post.assert_called_with(expected_path,
                expected_data, auth=expected_auth)


class UrlBuilderTestCase(unittest.TestCase):

    def setUp(self):
        self.app_secret = "12345"
        self.merchant_id = "123"
        self.app_id = "234234"
        mock_client = mock.Mock()
        mock_client.merchant_id = self.merchant_id
        mock_client._app_secret = self.app_secret
        mock_client._app_id = self.app_id
        mock_client.get_base_url.return_value = "https://gocardless.com"
        self.urlbuilder = urlbuilder.UrlBuilder(mock_client)

    def make_mock_params(self, paramdict):
        mock_params = mock.Mock()
        if not "resource_name" in paramdict:
            mock_params.resource_name = "aresource"
        else:
            mock_params.resource_name = paramdict.pop("resource_name")
        mock_params.to_dict.return_value = paramdict
        return mock_params

    def get_url_params(self, url):
        param_dict = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        return dict([[k,v[0]] for k,v in six.iteritems(param_dict)])

    def test_urlbuilder_url_contains_correct_parameters(self):
        params = self.make_mock_params({"resource_name": "bill",
                "amount":20.0,
                    "merchant_id":"merchid"})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = get_url_params(url)
        for k,v in six.iteritems(params.to_dict()):
            if k == "resource_name":
                continue
            self.assertEqual(urlparams["bill[{0}]".format(k)], str(v))

    def test_resource_name_is_singularized_in_url(self):
        params = self.make_mock_params({"resource_name":"bills", \
                "amount":20.0})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = get_url_params(url)
        self.assertTrue("bill[amount]" in urlparams)


    def test_add_merchant_id_to_limit(self):
        params = self.make_mock_params({"resource_name": "bill",
            "merchant_id":self.merchant_id})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = get_url_params(url)
        self.assertEqual(urlparams["bill[merchant_id]"], self.merchant_id)

    def test_url_contains_state(self):
        params = self.make_mock_params({})
        url = self.urlbuilder.build_and_sign(params, state="somestate")
        urlparams = get_url_params(url)
        self.assertEqual(urlparams["state"], "somestate")

    def test_url_contains_redirect(self):
        params = self.make_mock_params({})
        url = self.urlbuilder.build_and_sign(params, redirect_uri="http://somesuchplace.com")
        urlparams = get_url_params(url)
        self.assertEqual(urlparams["redirect_uri"], "http://somesuchplace.com")

    def test_url_contains_cancel(self):
        params = self.make_mock_params({})
        url = self.urlbuilder.build_and_sign(params,
                cancel_uri="http://cancel")
        urlparams = get_url_params(url)
        self.assertEqual(urlparams["cancel_uri"], "http://cancel")

    def test_url_contains_nonce(self):
        params = self.make_mock_params({"somekey":"someval"})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = get_url_params(url)
        self.assertIsNotNone(urlparams["nonce"])

    def test_url_nonce_is_random(self):
        params = self.make_mock_params({"somekey":"somval"})
        url1 = self.urlbuilder.build_and_sign(params)
        url2 = self.urlbuilder.build_and_sign(params)
        self.assertNotEqual(get_url_params(url1)["nonce"],\
                get_url_params(url2)["nonce"])

    def test_url_contains_client_id(self):
        params = self.make_mock_params({"somekey":"someval"})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = get_url_params(url)
        self.assertEqual(urlparams["client_id"], self.app_id)

    def test_url_contains_resource_name(self):
        params = self.make_mock_params({"resource_name" : "pre_authorizations"})
        url = self.urlbuilder.build_and_sign(params)
        path = urllib.parse.urlparse(url).path
        self.assertEqual(path, "/connect/pre_authorizations/new")

    def test_url_contains_timestamp(self):
        testdate = datetime.datetime.strptime("2010-01-01:0800", "%Y-%m-%d:%H%M")
        with patch('datetime.datetime'):
            datetime.datetime.utcnow.return_value = testdate
            params = self.make_mock_params({"somekey":"somval"})
            url = self.urlbuilder.build_and_sign(params)
            urlparams = get_url_params(url)
            self.assertEqual(urlparams["timestamp"], testdate.isoformat()[:-7] + "Z")

    def test_other_timezones_use_UTC(self):
        #set system time to a timezone which is different to UTC
        if "TZ" in os.environ:
            oldtime = os.environ["TZ"]
        else:
            oldtime = None
        os.environ["TZ"] = "US/Eastern"
        time.tzset()
        params = self.make_mock_params({})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = get_url_params(url)
        timestamp = datetime.datetime.strptime(urlparams["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
        #restore timezone
        if oldtime:
            os.environ["TZ"] = oldtime
        else:
            del os.environ["TZ"]
        time.tzset()
        #check that time is reasonably close to now.
        self.assertTrue(abs((datetime.datetime.utcnow() - timestamp).
            total_seconds()) < 100)

class MerchantUrlTestCase(unittest.TestCase):
    def setUp(self):
        self.client = create_mock_client(mock_account_details)
        self.mock_auth_code = ("DlydRBP+1iHjxPUBtNTtO5jCldrkbnrdhpaaVqiU1F4mkhwi"
            "MJQCNlAJ6fPSN65NY")
        self.access_token_response = {
                    "access_token":"thetoken",
                    "token_type":"bearer",
                    "scope":"manage_merchant:themanagedone"
                    }

    def test_merchant_url_parameters(self):
        url = self.client.new_merchant_url("http://someurl")
        params = get_url_params(url)
        expected = {
                "client_id":mock_account_details["app_id"],
                "redirect_uri":"http://someurl",
                "scope":"manage_merchant",
                "response_type":"code"
                }
        self.assertEqual(expected, params)

    def test_merchant_url_with_merchant_prepop(self):
        merchant = {
                "name":"merchname",
                "billing_address_1":"myadd1",
                "billing_address_2":"myadd2",
                "billing_town":"smalltown",
                "billing_county":"godknows",
                "billing_postcode":"PSTCDE",
                "user":{
                    "first_name":"nameone",
                    "last_name":"nametwo",
                    "email":"email@email.com"
                    }
                }
        url = self.client.new_merchant_url("http://someutl/somepath", merchant=merchant)
        params = get_url_params(url)
        self.assertEqual(params["merchant[name]"], "merchname")
        self.assertEqual(params["merchant[user][first_name]"], "nameone")

    def test_merchant_url_state(self):
        url = self.client.new_merchant_url("http://someurl", state="thestate")
        params = get_url_params(url)
        self.assertEqual(params["state"], "thestate")


    def test_fetch_client_access_token_basic_authorization(self):
        expected_data = {
                "client_id":mock_account_details["app_id"],
                "code":self.mock_auth_code,
                "redirect_uri":"http://someurl",
                "grant_type":"authorization_code"
                }
        query = utils.to_query(expected_data)
        expected_auth = (
            mock_account_details["app_id"],
            mock_account_details["app_secret"])
        with patch.object(self.client, '_request') as mock_request:
            mock_request.return_value = self.access_token_response
            self.client.fetch_access_token(expected_data["redirect_uri"],
                    self.mock_auth_code)
            mock_request.assert_called_with("post", "/oauth/"
                "access_token?{0}".format(query), auth=expected_auth)

    def test_fetch_client_sets_access_token_and_merchant_id(self):
        with patch.object(self.client, '_request') as mock_post:
            mock_post.return_value = self.access_token_response
            result = self.client.fetch_access_token("http://someuri",
                    "someauthcode")
            self.assertEqual(result, "thetoken")
            self.assertEqual(self.client._access_token, "thetoken")
            self.assertEqual(self.client._merchant_id, "themanagedone")


class Matcher(object):
    """Object for comparing objects with an arbitrary comparison function

    This is used as a matcher for testing properties of arguments in mocks
    see http://www.voidspace.org.uk/python/mock/examples.html#matching-any-argument-in-assertions
    """
    def __init__(self, func):
        self.func = func
    def __eq__(self, other):
        return self.func(other)

class ClientUrlBuilderTestCase(unittest.TestCase):
    """Integration test for the Client <-> UrlBuilder relationship

    Tests that the url building methods on the client correctly
    call methods on the urlbuilder class
    """

    def urlbuilder_argument_check(self, method, expected_type, *args):
        mock_inst = mock.Mock(urlbuilder.UrlBuilder)
        with patch('gocardless.urlbuilder.UrlBuilder') as mock_builder:
            mock_inst.build_and_sign.return_value = "http://someurl"
            mock_builder.return_value = mock_inst
            c = create_mock_client(mock_account_details)
            getattr(c, method)(*args)
            matcher = Matcher(lambda x: type(x) == expected_type)
            mock_inst.build_and_sign.assert_called_with(matcher,
                    cancel_uri=None, redirect_uri=None, state=None)

    def params_argument_check(self, method, params_class, *args, **kwargs):
        with patch('gocardless.urlbuilder.UrlBuilder') as mock_builder:
            with patch('gocardless.urlbuilder.{0}'.format(params_class.__name__)) as mock_class:
                c = create_mock_client(mock_account_details)
                getattr(c, method)(*args, **kwargs)
                arg1 = args[0]
                rest = args[1:]
                mock_class.assert_called_with(arg1,
                        mock_account_details["merchant_id"], *rest,
                        **kwargs)

    def test_new_preauth_calls_urlbuilder(self):
        self.urlbuilder_argument_check("new_preauthorization_url",
                urlbuilder.PreAuthorizationParams,
                3, 7, "day")

    def test_new_pre_auth_calls_urlbuilder(self):
        self.urlbuilder_argument_check("new_pre_authorization_url",
                urlbuilder.PreAuthorizationParams,
                3, 7, "day")

    def test_new_preauth_params_constructor(self):
        self.params_argument_check("new_preauthorization_url",
                urlbuilder.PreAuthorizationParams,
                3, 7, "day", expires_at=datetime.datetime.now(),
                name="aname", description="desc", interval_count=5,
                calendar_intervals=False, user={"somekey":"somval"},
                setup_fee=None, currency=None)

    def test_new_pre_auth_params_constructor(self):
        self.params_argument_check("new_pre_authorization_url",
                urlbuilder.PreAuthorizationParams,
                3, 7, "day", expires_at=datetime.datetime.now(),
                name="aname", description="desc", interval_count=5,
                calendar_intervals=False, user={"somekey":"somval"},
                setup_fee=None, currency=None)

    def test_new_bill_calls_urlbuilder(self):
        self.urlbuilder_argument_check("new_bill_url",
                urlbuilder.BillParams,
                4)

    def test_new_bill_params_constructor(self):
        self.params_argument_check("new_bill_url",
                urlbuilder.BillParams,
                10, name="aname", user={"key":"val"},
                description="adesc", currency=None)

    def test_new_subscription_calls_urlbuilder(self):
        self.urlbuilder_argument_check("new_subscription_url",
                urlbuilder.SubscriptionParams,
                10, 10, "day")

    def test_new_sub_params_constructor(self):
        self.params_argument_check("new_subscription_url",
                urlbuilder.SubscriptionParams,
                10, 23, "day", name="name", description="adesc",
                start_at=datetime.datetime.now(),
                expires_at=datetime.datetime.now() + datetime.timedelta(100),
                interval_count=20, user={"key":"val"}, setup_fee=20,
                currency=None)


