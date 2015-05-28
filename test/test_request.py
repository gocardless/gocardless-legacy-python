import unittest
import mock

#from gocardless import request
import gocardless.request


class RequestTestCase(unittest.TestCase):

    def setUp(self):
        self.request = gocardless.request.Request('get', 'http://test.com')

    def test_valid_method_allows_valid_methods(self):
        for method in ('get', 'post', 'put'):
            self.assertTrue(self.request._valid_method('get'))

    def test_valid_method_disallows_invalid_methods(self):
        self.assertFalse(self.request._valid_method('fake_method'))

    def test_use_bearer_auth_sets_auth_header(self):
        self.request.use_bearer_auth('token')
        self.assertEqual(self.request._opts['headers']['Authorization'],
                         'bearer token')

    def test_use_http_auth_sets_auth_details_in_opts(self):
        self.request.use_http_auth('user', 'pass')
        self.assertEqual(self.request._opts['auth'], ('user', 'pass'))

    def test_set_payload_ignores_null_payloads(self):
        self.request.set_payload(None)
        self.assertTrue('Content-Type' not in self.request._opts['headers'])
        self.assertTrue('data' not in self.request._opts)

    def test_set_payload_sets_content_type(self):
        self.request.set_payload({'a': 'b'})
        self.assertEqual(self.request._opts['headers']['Content-Type'],
                         'application/json')

    def test_set_payload_encodes_payload(self):
        self.request.set_payload({'a': 'b'})
        self.assertEqual(self.request._opts['data'], '{"a": "b"}')

    @mock.patch('gocardless.request.requests')
    def test_perform_calls_get_for_gets(self, mock_requests):
        mock_requests.get.return_value.content = '{"a": "b"}'
        self.request.perform()
        mock_requests.get.assert_called_once_with(mock.ANY, headers=mock.ANY)

    @mock.patch('gocardless.request.requests')
    def test_perform_passes_params_through(self, mock_requests):
        params = {'x': 'y'}
        request = gocardless.request.Request('get', 'http://test.com', params)
        mock_requests.get.return_value.content = '{"a": "b"}'
        request.perform()
        mock_requests.get.assert_called_once_with(mock.ANY, headers=mock.ANY,
                                                  params=params)

    @mock.patch('gocardless.request.requests')
    def test_perform_calls_post_for_posts(self, mock_requests):
        mock_requests.post.return_value.content = '{"a": "b"}'
        self.request._method = 'post'
        self.request.perform()
        mock_requests.post.assert_called_once_with(mock.ANY, headers=mock.ANY)

    @mock.patch('gocardless.request.requests.get')
    def test_perform_decodes_json(self, mock_get):
        response = mock.Mock()
        response.json = lambda: {"a": "b"}
        mock_get.return_value = response
        self.assertEqual(self.request.perform(), {'a': 'b'})

