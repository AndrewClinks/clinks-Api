from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ...item.models import Item
from ...menu_category.models import MenuCategory

from ..utils import Data, Manager

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.venue = Manager.create_venue()

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/menu-items", data, access_token)

        return response

    def test_with_adding_to_menu_with_categories(self):
        company = self.venue.company

        self.assertFalse(company.has_added_menu_items)

        Manager.setup_menu(with_menu_item=False)

        company.refresh_from_db()
        self.assertFalse(company.has_added_menu_items)

        data = Data.valid_menu_item_data(self.venue.menu)

        response = self._post(data, self.admin_access_token)

        menu_category = MenuCategory.objects.get(id=response.json["menu_category"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["item"]["id"], data["item"])
        self.assertEqual(response.json["item"]["subcategory"]["parent"], menu_category.category_id)
        self.assertEqual(response.json["order"], 0)
        self.assertEqual(response.json["price"], data["price"])
        self.assertEqual(response.json["price_sale"], data["price_sale"])

        company.refresh_from_db()
        self.assertTrue(company.has_added_menu_items)

        item = Item.objects.get(id=response.json["item"]["id"])

        self.assertEqual(item.menu_item_count, 1)

        self.assertEqual(item.subcategory.menu_item_count, 1)
        self.assertEqual(item.subcategory.item_count, 1)

        self.assertEqual(item.subcategory.parent.menu_item_count, 1)
        self.assertEqual(item.subcategory.parent.item_count, 1)

    def test_success_with_company_member(self):
        data = Data.valid_menu_item_data(self.venue.menu)

        staff = Manager.create_staff(venue=self.venue)

        access_token = Manager.get_access_token(staff.company_member.user)

        data["passcode"] = self.venue.company.passcode

        response = self._post(data, access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_failure_with_company_member_without_passcode(self):
        data = Data.valid_menu_item_data(self.venue.menu)

        staff = Manager.create_staff(venue=self.venue)

        access_token = Manager.get_access_token(staff.company_member.user)

        response = self._post(data, access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["passcode"][0], 'Passcode is required')

    def test_failure_with_company_member_incorrect_passcode(self):
        data = Data.valid_menu_item_data(self.venue.menu)

        staff = Manager.create_staff(venue=self.venue)

        access_token = Manager.get_access_token(staff.company_member.user)

        data["passcode"] = 9999999

        response = self._post(data, access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["passcode"][0], 'Incorrect passcode')

    def test_failure_with_member_belongs_to_different_company(self):
        data = Data.valid_menu_item_data(self.venue.menu)

        response = self._post(data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], 'You cannot edit this menu')

    def test_with_member_belongs_to_same_company_but_not_in_venue_staff(self):
        data = Data.valid_menu_item_data(self.venue.menu)

        access_token = Manager.get_company_member_access_token(company=self.venue.company)

        data["passcode"] = self.venue.company.passcode

        response = self._post(data, access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_failure_with_adding_to_menu_item_does_not_belong_to_menu(self):
        data = Data.valid_menu_item_data(self.venue.menu)
        data["menu"] = Manager.setup_menu().venue_id

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], 'This menu_category does not belong to this menu')

        menu_category = Manager.create_menu_category(menu=self.venue.menu)
        data["menu"] = self.venue.id
        data["menu_category"] = menu_category.id

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], 'This item does not  belong to this category')

    def test_failure_without_required_info(self):
        data = {}

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["menu"][0], 'This field is required.')
        self.assertEqual(response.json["price"][0], 'This field is required.')
        self.assertEqual(response.json["item"][0], 'This field is required.')
        self.assertEqual(response.json["menu_category"][0], 'This field is required.')
        self.assertEqual(response.json["currency"][0], 'This field is required.')

    def test_failure_with_price_sale_bigger_than_price(self):
        data = Data.valid_menu_item_data(self.venue.menu, price=1000, price_sale=2000)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], 'price_sale cannot be bigger than price')

    def test_failure_with_invalid_ids(self):
        data = {
            "menu": 9999,
            "menu_category": 9999,
            "item": 9999,
            "price": 1000,
            "currency": 9999,
        }

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["menu"][0], 'Invalid pk "9999" - object does not exist.')
        self.assertEqual(response.json["item"][0], 'Invalid pk "9999" - object does not exist.')
        self.assertEqual(response.json["menu_category"][0], 'Invalid pk "9999" - object does not exist.')
        self.assertEqual(response.json["currency"][0], 'Invalid pk "9999" - object does not exist.')

    def test_failure_with_item_does_not_belong_to_menu_category(self):
        data = Data.valid_menu_item_data(self.venue.menu)
        data["item"] = Manager.create_item().id

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], 'This item does not  belong to this category')

    def test_failure_with_deleted_item(self):
        from ...item.models import Item

        data = Data.valid_menu_item_data()
        item_id = data['item']

        Item.objects.filter(id=item_id).delete()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["item"][0], f'Invalid pk "{item_id}" - object does not exist.')

    def test_with_duplicate_menu_item(self):
        menu = Manager.setup_menu(venue=self.venue)

        data = Data.valid_menu_item_data(menu, menu.categories.first(), menu.categories.first().items.first().item)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_check_order(self):
        menu = Manager.setup_menu()

        menu_category = menu.categories.first()

        data = Data.valid_menu_item_data(menu, menu_category)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["order"], 1)

        data = Data.valid_menu_item_data(menu, menu_category)

        response = self._post(data, self.admin_access_token)

        menu_item_id_to_be_deleted = response.json["id"]

        self.assertEqual(response.json["order"], 2)

        response = super(CreateTest, self)._delete(f"/menu-items/{menu_item_id_to_be_deleted}", self.admin_access_token)

        data = Data.valid_menu_item_data(menu, menu_category)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.json["order"], 2)

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.permission_denied_test(self._post({}))
