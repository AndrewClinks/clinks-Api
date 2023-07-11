from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...card.models import Card

from ..utils import Data, Manager


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer = Manager.create_customer()
        self.customer_access_token = Manager.get_access_token(self.customer.user)

        self.card_1 = Manager.create_card(self.customer_access_token)

        self.card_2 = Manager.create_card(self.customer_access_token, Data.valid_card_data(default=False))

    def _get(self, access_token="", **kwargs):
        response = super()._get("/cards", access_token=access_token)

        return response

    def test_success(self):
        response = self._get(self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["results"][0]["id"], self.card_1.id)

        card_3 = Manager.create_card(self.customer_access_token)

        response = self._get(self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["results"][0]["id"], card_3.id)

        self.assertEqual(response.json["results"][1]["id"], self.card_2.id)

        self.assertEqual(response.json["results"][2]["id"], self.card_1.id)

    def test_with_an_account_without_card(self):
        access_token = Manager.get_customer_access_token()

        response = self._get(access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["results"], [])

    def test_failure_with_admin(self):
        self.permission_denied_test(self._get(access_token=Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(access_token=Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())


