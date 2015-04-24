""" E-Commerce API client """

import datetime
import logging

from django.conf import settings
import jwt
import requests
import slumber

from commerce.exceptions import InvalidConfigurationError


log = logging.getLogger(__name__)


class JwtAuth(requests.auth.AuthBase):
    def __init__(self, user, signing_key):
        self.user = user
        self.signing_key = signing_key

    def __call__(self, r):
        data = {
            'username': self.user.username,
            'email': self.user.email
        }

        r.headers['Authorization'] = 'JWT ' + jwt.encode(data, self.signing_key)
        return r


class EcommerceAPI(object):
    """ E-Commerce API client. """

    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self, user, url=None, key=None, timeout=None):
        url = url or settings.ECOMMERCE_API_URL
        key = key or settings.ECOMMERCE_API_SIGNING_KEY

        if not (url and key):
            raise InvalidConfigurationError('Values for both url and key must be set.')

        session = requests.Session()
        session.timeout = timeout or getattr(settings, 'ECOMMERCE_API_TIMEOUT', 5)
        self.api = slumber.API(url, session=session, auth=JwtAuth(user, key))

    def get_order(self, order_number):
        """
        Retrieve a paid order.

        Arguments
            user             --  User associated with the requested order.
            order_number     --  The unique identifier for the order.

        Returns a tuple with the order number, order status, API response data.
        """

        data = self.api.orders.get(order_number)
        data['date_placed'] = datetime.datetime.strptime(data['date_placed'], self.DATETIME_FORMAT)
        return data['number'], data['status'], data

    def get_processors(self):
        """
        Retrieve the list of available payment processors.

        Returns a list of strings.
        """

        return self.api.payment.processors.get()

    def create_basket(self, sku, payment_processor=None):
        """Create a new basket and immediately trigger checkout.

        Note that while the API supports deferring checkout to a separate step,
        as well as adding multiple products to the basket, this client does not
        currently need that capability, so that case is not supported.

        Args:
            user: the django.auth.User for which the basket should be created.
            sku: a string containing the SKU of the course seat being ordered.
            payment_processor: (optional) the name of the payment processor to
                use for checkout.

        Returns:
            A dictionary containing {id, order, payment_data}.

        Raises:
            TimeoutError: the request to the API server timed out.
            InvalidResponseError: the API server response was not understood.
        """

        data = {'products': [{'sku': sku}], 'checkout': True, 'payment_processor_name': payment_processor}
        return self.api.baskets.post(data)

    def get_basket_order(self, basket_id):
        """ Retrieve an order associated with a basket. """

        data = self.api.baskets(basket_id).order.get()
        data['date_placed'] = datetime.datetime.strptime(data['date_placed'], self.DATETIME_FORMAT)
        return data
