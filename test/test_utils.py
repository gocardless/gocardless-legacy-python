# coding: utf-8

import unittest
import six
import codecs


from gocardless import utils


class PercentEncodeTestCase(unittest.TestCase):

    def test_works_with_empty_strings(self):
      self.assertEqual(utils.percent_encode(six.u("")), six.u(""))

    def test_doesnt_encode_lowercase_alpha_characters(self):
      self.assertEqual(utils.percent_encode(six.u("abcxyz")), six.u("abcxyz"))

    def test_doesnt_encode_uppercase_alpha_characters(self):
      self.assertEqual(utils.percent_encode(six.u("ABCXYZ")), six.u("ABCXYZ"))

    def test_doesnt_encode_digits(self):
      self.assertEqual(utils.percent_encode(six.u("1234567890")), six.u("1234567890"))

    def test_doesnt_encode_unreserved_non_alphanum_chars(self):
      self.assertEqual(utils.percent_encode(six.u("-._~")), six.u("-._~"))

    def test_encodes_non_ascii_alpha_characters(self):
      if six.PY3:
          original = "å"
      else:
          original = codecs.lookup('utf-8').decode("å")[0]
      self.assertEqual(utils.percent_encode(original), six.u("%C3%A5"))

    def test_encodes_reserved_ascii_characters(self):
      self.assertEqual(utils.percent_encode(six.u(" !\"#$%&'()")),
                       six.u("%20%21%22%23%24%25%26%27%28%29"))
      self.assertEqual(utils.percent_encode(six.u("*+,/{|}:;")),
                       six.u("%2A%2B%2C%2F%7B%7C%7D%3A%3B"))
      self.assertEqual(utils.percent_encode(six.u("<=>?@[\\]^`")),
                       six.u("%3C%3D%3E%3F%40%5B%5C%5D%5E%60"))

    def test_encodes_other_non_ascii_characters(self):
      if six.PY3:
          original = "支払い"
      else:
          original = codecs.lookup('utf-8').decode("支払い")[0]
      self.assertEqual(utils.percent_encode(original),
                       six.u("%E6%94%AF%E6%89%95%E3%81%84"))


class SignatureTestCase(unittest.TestCase):
    def setUp(self):
      self.secret = '5PUZmVMmukNwiHc7V/TJvFHRQZWZumIpCnfZKrVYGpuAdkCcEfv3LIDSrsJ+xOVH'
      self.api_key = ''
      self.client_id = '4jqkF9tirkr3zfWCgEKxLDy3UmF1sWpHPVm8X69yiB7Lqb63usVOPzrm0jEepc5R'

    def test_hmac(self):
      # make sure our signature function
      # works correctly
      sig = utils.generate_signature({"foo": "bar", "example": [1, "a"]},self.secret)
      self.assertEqual(sig, '5a9447aef2ebd0e12d80d80c836858c6f9c13219f615ef5d135da408bcad453d')

    def test_validate_signature(self):
        params = {"key1":"val1", "key2":"val2"}
        sig = utils.generate_signature(params, self.secret)
        params["signature"] = sig
        self.assertTrue(utils.signature_valid(params, self.secret))
        params["signature"] = "123482494523435"
        self.assertFalse(utils.signature_valid(params, self.secret))


class CamelizeTestCase(unittest.TestCase):
    def test_camelize_multi_word(self):
        teststr = "camelize_this_please"
        expected = "CamelizeThisPlease"
        self.assertEqual(expected, utils.camelize(teststr))


class SingularizeTestCase(unittest.TestCase):
    def test_singularize(self):
        to_singularize = "PreAuthorisations"
        expected = "PreAuthorisation"
        self.assertEqual(expected, utils.singularize(to_singularize))


