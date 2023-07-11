from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...company.models import Company

from ...utils import Constants


class EditTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.menu = Manager.setup_menu()

        self.menu_category = self.menu.categories.first()

        self.menu_item = self.menu_category.items.first()

        self.menu_item_id = self.menu_item.id

    def _patch(self, id, data, access_token="", passcode=None, **kwargs):
        endpoint = f"/menu-items/{id}"

        if passcode:
            endpoint += f"?passcode={passcode}"

        response = super()._patch(endpoint, data, access_token)

        return response

    def test_with_admin(self):
        data = {
            "price": 2000,
            "price_sale": 1000,
            "item": Manager.create_item(subcategory=Manager.create_subcategory(parent=self.menu_category.category)).id,
            "menu_category": Manager.create_menu_category().id
        }

        response = self._patch(self.menu_item_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["item"]["id"], data["item"])
        self.assertEqual(response.json["price"], data["price"])
        self.assertEqual(response.json["price_sale"], data["price_sale"])
        self.assertNotEqual(response.json["menu_category"], data["menu_category"])

    def test_success_with_company_member(self):
        data = {
            "price": 2000,
            "price_sale": 1000,
            "item": Manager.create_item(subcategory=Manager.create_subcategory(parent=self.menu_category.category)).id,
            "menu_category": Manager.create_menu_category().id
        }

        access_token = Manager.get_staff_access_token(self.menu.venue)

        response = self._patch(self.menu_item_id, data, access_token, self.menu.venue.company.passcode)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["item"]["id"], data["item"])
        self.assertEqual(response.json["price"], data["price"])
        self.assertEqual(response.json["price_sale"], data["price_sale"])
        self.assertNotEqual(response.json["menu_category"], data["menu_category"])

    def test_failure_with_company_member_without_passcode(self):
        data = {
            "price": 2000,
            "price_sale": 1000,
            "item": Manager.create_item(subcategory=Manager.create_subcategory(parent=self.menu_category.category)).id,
            "menu_category": Manager.create_menu_category().id
        }

        access_token = Manager.get_staff_access_token(self.menu.venue)

        response = self._patch(self.menu_item_id, data, access_token)

        self.assertEqual(response.json["detail"], 'passcode is required.')

    def test_failure_with_company_member_incorrect_passcode(self):
        data = {
            "price": 2000,
            "price_sale": 1000,
            "item": Manager.create_item(subcategory=Manager.create_subcategory(parent=self.menu_category.category)).id,
            "menu_category": Manager.create_menu_category().id
        }

        access_token = Manager.get_staff_access_token(self.menu.venue)

        response = self._patch(self.menu_item_id, data, access_token, 999999)

        self.assertEqual(response.json["detail"], 'Incorrect passcode')

    def test_failure_with_editing_item_to_a_item_does_not_belong_to_category(self):
        data = {
            "item": Manager.create_item().id
        }

        response = self._patch(self.menu_item_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], 'This item does not belong to this category')

    def test_with_duplicate_menu_item(self):
        menu_item = Manager.create_menu_item(menu=self.menu, menu_category=self.menu_category)

        data = {
            "item": Manager.create_item(subcategory=menu_item.item.subcategory).id
        }

        response = self._patch(self.menu_item_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.menu_category.refresh_from_db()

        self.assertEqual(self.menu_category.items.count(), 2)

    def test_failure_with_member_belongs_to_different_company(self):
        response = self._patch(self.menu_item_id, {}, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_failure_with_member_belongs_to_same_company_but_not_in_venue_staff(self):
        access_token = Manager.get_company_member_access_token(company=self.menu.venue.company)

        response = self._patch(self.menu_item_id, {}, access_token, self.menu.venue.company.passcode)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_staff_not_in_venue_staff(self):
        access_token = Manager.get_staff_access_token(company=self.menu.venue.company)

        response = self._patch(self.menu_item_id, {}, access_token, self.menu.venue.company.passcode)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_setting_price_less_than_price_sale(self):
        data = {
            "price_sale": self.menu_item.price + 1000
        }

        response = self._patch(self.menu_item_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], 'price_sale cannot be bigger than price')

        data = {
            "price_sale": self.menu_item.price
        }

        response = self._patch(self.menu_item_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], 'price_sale cannot be bigger than price')

        data = {
            "price_sale": self.menu_item.price - 200
        }

        response = self._patch(self.menu_item_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            "price": response.json["price_sale"] - 500
        }

        response = self._patch(self.menu_item_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], 'price cannot be less than price_sale')

        data = {
            "price": 0,
            "price_sale": None
        }

        response = self._patch(self.menu_item_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            "price": -100,
        }

        response = self._patch(self.menu_item_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["price"][0], 'Ensure this value is greater than or equal to 0.')

    def test_failure_with_customer(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))