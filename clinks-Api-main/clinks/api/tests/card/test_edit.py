from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...card.models import Card

from ..utils import Data, Manager


class EditTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer = Manager.create_customer()
        self.customer_access_token = Manager.get_access_token(self.customer.user)

        self.card = Manager.create_card(self.customer_access_token)

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/cards/{id}", data, access_token)

        return response

    def test_change_non_default_to_default(self):
        data = Data.valid_card_data(default=False)

        card = Manager.create_card(self.customer_access_token, data)

        self.assertTrue(self.card.default)

        self.assertFalse(card.default)

        update_data = {
            "default": True
        }

        response = self._patch(card.id, update_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["id"], card.id)

        self.assertTrue(response.json["default"])

        self.card = Card.objects.get(id=self.card.id)

        self.assertFalse(card.default)

    def test_change_default_to_non_default(self):
        update_data = {
            "default": False
        }

        response = self._patch(self.card.id, update_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(response.json["default"])

    def test_failure_without_default(self):
        response = self._patch(self.card.id, {}, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["default"][0], 'This field is required.')

    def test_failure_with_editing_basic_card_info(self):
        update_data = {
            "last4": 1111,
            "name": "name",
            "brand": "brand",
            "default": True
        }

        response = self._patch(self.card.id, update_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotEqual(response.json["last4"], update_data["last4"])

        self.assertNotEqual(response.json["name"], update_data["name"])

        self.assertNotEqual(response.json["brand"], update_data["brand"])

        self.assertEqual(response.json["default"], update_data["default"])

    def test_failure_edit_card_belongs_to_someone_else(self):
        update_data = {
            "default": True
        }

        access_token = Manager.get_customer_access_token()

        response = self._patch(self.card.id, update_data, access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_admin(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))