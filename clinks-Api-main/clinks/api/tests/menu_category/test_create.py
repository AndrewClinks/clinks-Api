from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.venue = Manager.create_venue()

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/menu-categories", data, access_token)

        return response

    def test_success_with_admin(self):
        data = Data.valid_menu_category_data(menu=self.venue.menu)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["menu_items"], [])

        self.assertEqual(response.json["category"]["id"], data["category"])

        self.assertEqual(response.json["order"], 0)

        self.assertEqual(response.json["menu"], self.venue.id)

    def test_success_with_company_member(self):
        data = Data.valid_menu_category_data(menu=self.venue.menu, include_passcode=True)

        access_token = Manager.get_staff_access_token(self.venue)

        response = self._post(data, access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["menu_items"], [])

        self.assertEqual(response.json["category"]["id"], data["category"])

        self.assertEqual(response.json["order"], 0)

        self.assertEqual(response.json["menu"], self.venue.id)

    def test_check_order(self):
        data = Data.valid_menu_category_data(self.venue.menu)

        response = self._post(data, self.admin_access_token)

        menu_category_id_to_be_deleted = response.json["id"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["order"], 0)

        data = Data.valid_menu_category_data(self.venue.menu)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["order"], 1)

        response = super(CreateTest, self)._delete(f"/menu-categories/{menu_category_id_to_be_deleted}", self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        data = Data.valid_menu_category_data(self.venue.menu)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["order"], 2)

        response = super(CreateTest, self)._delete(f"/menu-categories/{response.json['id']}",
                                             self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        data = Data.valid_menu_category_data(self.venue.menu)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["order"], 2)

    def test_with_staff_does_not_belong_venue(self):
        data = Data.valid_menu_category_data(menu=self.venue.menu, include_passcode=True)

        access_token = Manager.get_staff_access_token(company=self.venue.company)

        response = self._post(data, access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_failure_with_subcategory_as_menu_category(self):
        data = Data.valid_menu_category_data(category=Manager.create_subcategory())

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["category"]["MenuCategory"], 'Given category is a subcategory')

    def test_failure_without_required_fields(self):
        data = {}

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["menu"][0], 'This field is required.')
        self.assertEqual(response.json["category"][0], 'This field is required.')

    def test_failure_with_company_member_without_passcode(self):
        data = Data.valid_menu_category_data(menu=self.venue.menu)

        access_token = Manager.get_staff_access_token(self.venue)

        response = self._post(data, access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["passcode"][0], 'Passcode is required')

    def test_failure_with_company_member_incorrect_passcode(self):
        data = Data.valid_menu_category_data(menu=self.venue.menu)

        data["passcode"] = 99999999

        access_token = Manager.get_staff_access_token(self.venue)

        response = self._post(data, access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["passcode"][0], 'Incorrect passcode')

    def test_failure_with_duplicate_menu_category(self):
        menu = Manager.setup_menu()

        data = Data.valid_menu_category_data(menu=menu, category=menu.categories.first().category)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuCategory"][0], 'A menu category with this category already exists')

    def test_failure_with_member_belongs_to_different_company(self):
        data = Data.valid_menu_category_data(menu=self.venue.menu)

        response = self._post(data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["MenuItem"][0], "You cannot edit this menu")

    def test_failure_with_invalid_ids(self):
        data = Data.valid_menu_category_data(self.venue.menu)
        data["menu"] = 9999
        data["category"] = 9999

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["menu"][0], 'Invalid pk "9999" - object does not exist.')
        self.assertEqual(response.json["category"][0], 'Invalid pk "9999" - object does not exist.')

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._post({}))
