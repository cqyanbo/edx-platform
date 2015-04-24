""" Tests the E-Commerce API module. """

import json

from ddt import ddt, data
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
from django.test.utils import override_settings
import httpretty
from slumber.exceptions import SlumberHttpBaseException

from commerce.api import EcommerceAPI
from commerce.exceptions import InvalidConfigurationError
from commerce.tests import EcommerceApiTestMixin
from student.tests.factories import UserFactory


@ddt
@override_settings(ECOMMERCE_API_URL=EcommerceApiTestMixin.ECOMMERCE_API_URL,
                   ECOMMERCE_API_SIGNING_KEY=EcommerceApiTestMixin.ECOMMERCE_API_SIGNING_KEY)
class EcommerceAPITests(EcommerceApiTestMixin, TestCase):
    """ Tests for the E-Commerce API client. """

    SKU = '1234'

    def setUp(self):
        super(EcommerceAPITests, self).setUp()
        self.url = reverse('commerce:baskets')
        self.user = UserFactory()
        self.api = EcommerceAPI(self.user)

    @override_settings(ECOMMERCE_API_URL=None, ECOMMERCE_API_SIGNING_KEY=None)
    def test_no_settings(self):
        """
        If the settings ECOMMERCE_API_URL and ECOMMERCE_API_SIGNING_KEY are invalid, the constructor should
        raise a ValueError.
        """
        self.assertRaises(InvalidConfigurationError, EcommerceAPI, self.user)

    @httpretty.activate
    @data(True, False)
    def test_create_basket(self, is_payment_required):
        """ Verify the method makes a call to the E-Commerce API with the correct headers and data. """
        self._mock_ecommerce_api(is_payment_required=is_payment_required)
        response_data = self.api.create_basket(self.SKU, self.PROCESSOR)

        # Validate the request sent to the E-Commerce API endpoint.
        request = httpretty.last_request()
        self.assertValidBasketRequest(request, self.user, self.ECOMMERCE_API_SIGNING_KEY, self.SKU, self.PROCESSOR)

        # Validate the data returned by the method
        print response_data
        self.assertEqual(response_data['id'], self.BASKET_ID)
        if is_payment_required:
            self.assertEqual(response_data['order'], None)
            self.assertEqual(response_data['payment_data'], self.PAYMENT_DATA)
        else:
            self.assertEqual(response_data['order'], {"number": self.ORDER_NUMBER})
            self.assertEqual(response_data['payment_data'], None)

    @httpretty.activate
    @data(400, 401, 405, 406, 429, 500, 503)
    def test_create_basket_with_invalid_http_status(self, status):
        """ If the E-Commerce API returns a non-200 status, the method should raise an InvalidResponseError. """
        self._mock_ecommerce_api(status=status, body=json.dumps({'user_message': 'FAIL!'}))
        self.assertRaises(SlumberHttpBaseException, self.api.create_basket, self.SKU, self.PROCESSOR)
