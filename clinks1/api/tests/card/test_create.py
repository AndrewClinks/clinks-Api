from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...card.models import Card

from ..utils import Data, Manager


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer = Manager.create_customer()

        self.customer_access_token = Manager.get_access_token(self.customer.user)

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/cards", data, access_token)

        return response

    def test_success(self):
        data = Data.valid_card_data()

        response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(response.json["default"])

    def test_with_multiple(self):
        data = Data.valid_card_data()

        response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(response.json["default"])

        first_card_id = response.json["id"]

        data = Data.valid_card_data()

        response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(response.json["default"])

        second_card_id = response.json["id"]

        first_card = Card.objects.get(id=first_card_id)

        self.assertFalse(first_card.default)

        data = Data.valid_card_data(default=False)

        response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertFalse(response.json["default"])

        first_card = Card.objects.get(id=first_card_id)

        self.assertFalse(first_card.default)

        second_card = Card.objects.get(id=second_card_id)

        self.assertTrue(second_card.default)

        self.assertEqual(Card.objects.filter(customer=self.customer).count(), 3)

    def test_with_false_default(self):
        data = Data.valid_card_data(default=False)

        response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(response.json["default"])

    def test_failure_with_invalid_payment_id(self):
        data = Data.valid_card_data("ERROR")

        response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue("No such PaymentMethod: 'ERROR'" in response.json["card"]["detail"])

    def test_failure_with_admin(self):
        self.permission_denied_test(self._post({}, Manager.get_admin_access_token()))



    def test_failure_with_company_member(self):
        self.permission_denied_test(self._post({}, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._post({}))