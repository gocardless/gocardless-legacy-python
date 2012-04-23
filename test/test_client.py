import base64
import datetime
import json
import unittest
import mock
from mock import patch
import sys
import urlparse

import gocardless
from gocardless.client import Client
from gocardless import utils
from gocardless import urlbuilder
from gocardless.exceptions import SignatureError
from test_resources import create_mock_attrs

merchant_json = json.loads("""{
   "created_at": "2011-11-18T17:07:09Z",
   "description": null,
   "id": "WOQRUJU9OH2HH1",
   "name": "Tom's Delicious Chicken Shop",
   "first_name": "Tom",
   "last_name": "Blomfield",
   "email": "tom@gocardless.com",
   "uri": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1",
   "balance": "12.00",
   "pending_balance": "0.00",
   "next_payout_date": "2011-11-25T17: 07: 09Z",
   "next_payout_amount": "12.00",
   "sub_resource_uris": {
      "users": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/users",
      "bills": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/bills",
      "pre_authorizations": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/pre_authorizations",
      "subscriptions": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/subscriptions"
   }
}
""")

subscription_json = json.loads("""
{
   "amount":"44.0",
   "interval_length":1,
   "interval_unit":"month",
   "created_at":"2011-09-12T13:51:30Z",
   "currency":"GBP",
   "name":"London Gym Membership",
   "description":"Entitles you to use all of the gyms around London",
   "expires_at":null,
   "next_interval_start":"2011-10-12T13:51:30Z",
   "id": "AJKH638A99",
   "merchant_id":"WOQRUJU9OH2HH1",
   "status":"active",
   "user_id":"HJEH638AJD",
   "uri":"https://gocardless.com/api/v1/subscriptions/1580",
   "sub_resource_uris":{
      "bills":"https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/bills?source_id=1580"
   }
}
""")

mock_account_details = {
            'app_id': 'id01',
            'app_secret': 'sec01',
            'token': 'tok01',
            'merchant_id': merchant_json["id"],
        }

class ClientTestCase(unittest.TestCase):

    def setUp(self):
        self.account_details = mock_account_details.copy()
        self.client = Client(**self.account_details)

    def test_base_url_returns_the_correct_url_for_production(self):
      gocardless.environment = 'production'
      self.assertEqual(Client.get_base_url(), 'https://gocardless.com')

    def test_base_url_returns_the_correct_url_for_sandbox(self):
      gocardless.environment = 'sandbox'
      self.assertEqual(Client.get_base_url(), 'https://sandbox.gocardless.com')

    def test_base_url_returns_the_correct_url_when_set_manually(self):
      Client.base_url = 'https://abc.gocardless.com'
      self.assertEqual(Client.get_base_url(), 'https://abc.gocardless.com')

    def test_app_id_required(self):
        self.account_details.pop('app_id')
        with self.assertRaises(ValueError):
            Client(**self.account_details)

    def test_app_secret_required(self):
        self.account_details.pop('app_secret')
        with self.assertRaises(ValueError):
            Client(**self.account_details)

    def test_get_merchant(self):
        with patch.object(self.client, 'api_get'):
            self.client.api_get.return_value = merchant_json
            merchant = self.client.merchant()
            self.assertEqual(merchant.id, self.account_details["merchant_id"])

    def test_get_subscription(self):
        self.get_resource_tester("subscription", subscription_json)

    def test_get_user(self):
        self.get_resource_tester("user", create_mock_attrs({}))

    def test_get_pre_authorization(self):
        self.get_resource_tester("pre_authorization", create_mock_attrs({}))

    def test_get_bill(self):
        self.get_resource_tester("bill", create_mock_attrs({}))

    def get_resource_tester(self, resource_name, resource_fixture):
        expected_klass = getattr(sys.modules["gocardless.resources"], utils.camelize(resource_name))
        with patch.object(self.client, 'api_get'):
            self.client.api_get.return_value = resource_fixture
            obj = getattr(self.client, resource_name)("1")
            self.assertEqual(resource_fixture["id"], obj.id)
            self.assertIsInstance(obj, expected_klass)

class ConfirmResourceTestCase(unittest.TestCase):

    def setUp(self):
        self.client = Client(**mock_account_details)
        self.params =  {
                "resource_uri":"http://aresource",
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
            expected_auth = base64.b64encode("{0}:{1}".format(
                mock_account_details["app_id"],
                mock_account_details["app_secret"]))
            self.client.confirm_resource(self.params)
            mock_post.assert_called_with(self.params["resource_uri"], 
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
        param_dict = urlparse.parse_qs(urlparse.urlparse(url).query)
        return dict([[k,v[0]] for k,v in param_dict.items()])

    def test_urlbuilder_url_contains_correct_parameters(self):
        params = self.make_mock_params({"resource_name": "bill",
                "amount":20.0,
                    "merchant_id":"merchid"})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = self.get_url_params(url)
        for k,v in params.to_dict().items():
            if k == "resource_name":
                continue
            self.assertEqual(urlparams["bill[{0}]".format(k)], str(v))

    def test_resource_name_is_singularized_in_url(self):
        params = self.make_mock_params({"resource_name":"bills", \
                "amount":20.0})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = self.get_url_params(url)
        self.assertTrue(urlparams.has_key("bill[amount]"))
        

    def test_add_merchant_id_to_limit(self):
        params = self.make_mock_params({"resource_name": "bill",
            "merchant_id":self.merchant_id})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = self.get_url_params(url)
        self.assertEqual(urlparams["bill[merchant_id]"], self.merchant_id)

    def test_url_contains_state(self):
        params = self.make_mock_params({})
        url = self.urlbuilder.build_and_sign(params, state="somestate")
        urlparams = self.get_url_params(url)
        self.assertEqual(urlparams["state"], "somestate")

    def test_url_contains_redirect(self):
        params = self.make_mock_params({})
        url = self.urlbuilder.build_and_sign(params, redirect_uri="http://somesuchplace.com")
        urlparams = self.get_url_params(url)
        self.assertEqual(urlparams["redirect_uri"], "http://somesuchplace.com")

    def test_url_contains_cancel(self):
        params = self.make_mock_params({})
        url = self.urlbuilder.build_and_sign(params, 
                cancel_uri="http://cancel")
        urlparams = self.get_url_params(url)
        self.assertEqual(urlparams["cancel_uri"], "http://cancel")

    def test_url_contains_nonce(self):
        params = self.make_mock_params({"somekey":"someval"})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = self.get_url_params(url)
        self.assertIsNotNone(urlparams["nonce"])

    def test_url_nonce_is_random(self):
        params = self.make_mock_params({"somekey":"somval"})
        url1 = self.urlbuilder.build_and_sign(params)
        url2 = self.urlbuilder.build_and_sign(params)
        self.assertNotEqual(self.get_url_params(url1)["nonce"],\
                self.get_url_params(url2)["nonce"])

    def test_url_contains_client_id(self):
        params = self.make_mock_params({"somekey":"someval"})
        url = self.urlbuilder.build_and_sign(params)
        urlparams = self.get_url_params(url)
        self.assertEqual(urlparams["client_id"], self.app_id)

    def test_url_contains_resource_name(self):
        params = self.make_mock_params({"resource_name" : "pre_authorizations"})
        url = self.urlbuilder.build_and_sign(params)
        path = urlparse.urlparse(url).path
        self.assertEqual(path, "/connect/pre_authorizations/new")

    def test_url_contains_timestamp(self):
        testdate = datetime.datetime.strptime("2010-01-01:0800", "%Y-%m-%d:%H%M")
        with patch('datetime.datetime'):
            datetime.datetime.now.return_value = testdate
            params = self.make_mock_params({"somekey":"somval"})
            url = self.urlbuilder.build_and_sign(params)
            urlparams = self.get_url_params(url)
            self.assertEqual(urlparams["timestamp"], testdate.isoformat()[:-7] + "Z")



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
            c = Client(**mock_account_details)
            getattr(c, method)(*args)
            matcher = Matcher(lambda x: type(x) == expected_type)
            mock_inst.build_and_sign.assert_called_with(matcher)
    
    def test_new_preauth_calls_urlbuilder(self):
        self.urlbuilder_argument_check("new_preauthorization_url", 
                urlbuilder.PreAuthorizationParams,
                3, 7, "day")
        
    def test_new_bill_calls_urlbuilder(self):
        self.urlbuilder_argument_check("new_bill_url",
                urlbuilder.BillParams,
                4)

    def test_new_subscription_calls_urlbuilder(self):
        self.urlbuilder_argument_check("new_subscription_url",
                urlbuilder.SubscriptionParams,
                10, 10, "day")







