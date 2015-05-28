import copy
import datetime
import json
import mock
from mock import patch
import unittest

import six

from . import fixtures
import gocardless
from gocardless.resources import Resource, Subscription, Bill, PreAuthorization
import collections


class TestResource(Resource):
    endpoint = "/testendpoint/:id"

    def __init__(self, attrs, client):
        attrs = create_mock_attrs(attrs)
        Resource.__init__(self, attrs, client)


class TestSubResource(Resource):
    endpoint = "/subresource/:id"


class OtherTestSubResource(Resource):
    endpoint = "/subresource2/:id"


def create_mock_attrs(to_merge):
    """
    Creats an attribute set for creating a resource from,
    includes the basic created, modified and id keys. Merges
    that with to_merge
    """
    attrs = {
        "created_at": "2012-04-18T17:53:12Z",
        "id": "1",
        "merchant_id": "amerchantid"
    }
    attrs.update(to_merge)
    return attrs


class ResourceTestCase(unittest.TestCase):

    def test_endpoint_declared_by_class(self):
        resource = TestResource({"id":"1"}, None)
        self.assertEqual(resource.get_endpoint(), "/testendpoint/1")

    def test_resource_attributes(self):
        attrs = {"key1":"one",
                "key2":"two",
                "key3":"three",
                "id":"1"}
        res = TestResource(attrs.copy(), None)
        for key, value in six.iteritems(attrs):
            self.assertEqual(getattr(res, key), value)

    def test_resource_created_at_is_date(self):
        created = datetime.datetime.strptime('2012-04-18T17:53:12Z',\
                "%Y-%m-%dT%H:%M:%SZ")
        attrs = create_mock_attrs({"created_at":'2012-04-18T17:53:12Z',
               "id":"1"})
        res = TestResource(attrs, None)
        self.assertEqual(res.created_at, created)

    def test_resources_with_equal_attrs_are_equal(self):
        attrs = create_mock_attrs({
            "someattr":"someval"
            })
        res1 = TestResource(attrs, None)
        res2 = TestResource(attrs, None)
        self.assertEqual(res1, res2)
        self.assertEqual(hash(res1), hash(res2))

class ResourceSubresourceTestCase(unittest.TestCase):

    def setUp(self):
        self.resource = TestResource({"sub_resource_uris":
            {"test_sub_resources":
                "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/bills?\
                        source_id=1580",
             "other_test_sub_resources": "aurl"},
            "id":"1"},
            None)

    def test_resource_lists_subresources(self):
        self.assertTrue(hasattr(self.resource, "test_sub_resources"))
        self.assertTrue(isinstance(getattr(self.resource, "test_sub_resources"), collections.Callable))

    def test_resource_subresource_returns_subresource_instances(self):
        mock_return = list(map(create_mock_attrs, [{"id":1},{"id":2}]))
        mock_client = mock.Mock()
        mock_client.api_get.return_value = mock_return
        self.resource.client = mock_client
        result = self.resource.test_sub_resources()
        for res in result:
            self.assertIsInstance(res, TestSubResource)
        self.assertEqual(set([1,2]), set([item.id for item in result]))

    def test_resource_can_query_subresource_with_params(self):
        mock_client = mock.Mock()
        mock_client.api_get.return_value = [create_mock_attrs({"id":"1"})]
        self.resource.client = mock_client
        result = self.resource.test_sub_resources(foo='bar')
        mock_client.api_get.assert_called_with(mock.ANY, params={'foo': 'bar'})

    def test_resource_is_correct_instance(self):
        """
        Expose an issue where the closure which creates sub_resource functions
        in the `Resource` constructor does not close over the class name
        correctly and thus every sub_resource function ends up referencing
        the same class.
        """
        mock_client = mock.Mock()
        mock_client.api_get.return_value = [create_mock_attrs({"id":"1"})]
        self.resource.client = mock_client
        result = self.resource.test_sub_resources()
        self.assertIsInstance(result[0], TestSubResource)


class FindResourceTestCase(unittest.TestCase):

    def test_find_resource_by_id_with_client(self):
        client = mock.Mock()
        client.api_get.return_value = {"id":"1"}
        resource = TestResource.find_with_client("1", client)
        self.assertEqual(resource.id, "1")

    def test_find_resource_without_details_throws_clienterror(self):
        old_client = gocardless.client
        gocardless.client = None
        self.assertRaises(gocardless.exceptions.ClientError, TestResource.find, "1")
        gocardless.client = old_client

    @patch('gocardless.client')
    def test_find_resource_without_client(self, mock_client):
        mock_client.api_get.return_value = {"id":"1"}
        self.assertEqual(TestResource.find("1").id, "1")



class TestDateResource(Resource):
    endpoint = "/dates"
    date_fields = ["modified", "activated"]


class DateResourceFieldTestCase(unittest.TestCase):

    def test_date_fields_are_converted(self):
        mod_date = datetime.datetime.strptime("2020-10-10T01:01:00", "%Y-%m-%dT%H:%M:%S")
        act_date = datetime.datetime.strptime("2020-10-10T01:01:03", "%Y-%m-%dT%H:%M:%S")
        params = {
            "modified":mod_date.isoformat() + "Z",
            "activated":act_date.isoformat() + "Z"
        }
        res = TestDateResource(create_mock_attrs(params), None)
        self.assertEqual(res.modified, mod_date)
        self.assertEqual(res.activated, act_date)


class TestReferenceResource(Resource):
    endpoint = "/referencing"
    reference_fields = ["test_resource_id"]
    date_fields = []

class ReferenceResourceTestCase(unittest.TestCase):

    def test_reference_fields_are_converted(self):
        params = create_mock_attrs({"test_resource_id":"2345"})
        res = TestReferenceResource(params, None)
        self.assertTrue(hasattr(res, "test_resource"))
        self.assertTrue(callable, res.test_resource)

    def test_reference_function_calls_resource(self):
        params = create_mock_attrs({"test_resource_id":"2345"})
        res = TestReferenceResource(params, None)
        with patch.object(TestResource,
                'find_with_client') as mock_res:
            mock_res.return_value = "1234"
            self.assertEqual("1234", res.test_resource())
            mock_res.assert_called_with("2345", None)

    def test_date_fields_inherited(self):
        params = create_mock_attrs({"test_resource_id":"123"})
        res = TestReferenceResource(params, None)
        self.assertIsInstance(res.created_at, datetime.datetime)

    def test_date_with_null_attr_does_not_throw(self):
        params = create_mock_attrs({"modified_at":None})
        testclass = type("TestModResource", (Resource,),
                {"date_fields":["modified_at"]})
        res = testclass(params, None)


class SubscriptionCancelTestCase(unittest.TestCase):

    def test_cancel_puts(self):
        client = mock.Mock()
        sub = Subscription(fixtures.subscription_json, client)
        sub.cancel()
        client.api_put.assert_called_with("/subscriptions/{0}/cancel".format(
            fixtures.subscription_json["id"]))

class PreAuthCancelTestCase(unittest.TestCase):

    def test_cancel_puts(self):
        client = mock.Mock()
        preauth= PreAuthorization(fixtures.preauth_json, client)
        preauth.cancel()
        client.api_put.assert_called_with(
                "/pre_authorizations/{0}/cancel".format(
                    fixtures.preauth_json["id"]))


class PreAuthBillCreationTestCase(unittest.TestCase):

    def test_create_bill_calls_client_api_post(self):
        client = mock.Mock()
        client.api_post.return_value = fixtures.bill_json
        result = Bill.create_under_preauth(10, "1234", client, name="aname",
                description="adesc", charge_customer_at="2013-08-27")
        self.assertIsInstance(result, Bill)
        expected_params = {
                "bill":{
                    "amount":10,
                    "pre_authorization_id":"1234",
                    "name":"aname",
                    "description":"adesc",
                    "charge_customer_at": "2013-08-27"
                    }
                }
        client.api_post.assert_called_with("/bills", expected_params)

    @patch('gocardless.resources.Bill')
    def test_preauth_create_calls_bill_create(self, mock_bill_class):
       pre_auth = PreAuthorization(fixtures.preauth_json, None)
       pre_auth.create_bill(10, name="aname", description="adesc",
                            charge_customer_at="2013-08-27")
       mock_bill_class.create_under_preauth.assert_called_with(10,
               pre_auth.id, None, name="aname",
               description="adesc", charge_customer_at="2013-08-27", currency=None)

class BillRetryTestCase(unittest.TestCase):

    def test_retry_post(self):
        client = mock.Mock()
        bill = Bill(fixtures.bill_json, client)
        bill.retry()
        retry_url = "/bills/{0}/retry".format(fixtures.bill_json["id"])
        client.api_post.assert_called_with(retry_url)

    def test_cancel_put(self):
        client = mock.Mock()
        bill = Bill(fixtures.bill_json, client)
        bill.cancel()
        cancel_url = "/bills/{0}/cancel".format(fixtures.bill_json["id"])
        client.api_put.assert_called_with(cancel_url)

    def test_refund_post(self):
        client = mock.Mock()
        bill = Bill(fixtures.bill_json, client)
        bill.refund()
        refund_url = "/bills/{0}/refund".format(fixtures.bill_json["id"])
        client.api_post.assert_called_with(refund_url)
