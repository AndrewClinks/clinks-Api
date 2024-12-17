from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.menu = Manager.setup_menu()

        self.menu_category_id = self.menu.categories.first().id

    def _get(self, id, access_token="", query_params_dict=None, **kwargs):
        response = super()._get(f"/menu-categories/{id}", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        response = self._get(self.menu_category_id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        menu_items = response.json["menu_items"]

        self.assertEqual(len(menu_items), 1)

    def test_success_with_company_member(self):
        access_token = Manager.get_staff_access_token(venue=self.menu.venue)

        query_params_dict = {
            "passcode": self.menu.venue.company.passcode
        }

        response = self._get(self.menu_category_id, access_token, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_member_belongs_to_different_company(self):
        response = self._get(self.menu_category_id, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_staff_does_not_belong_venue(self):
        access_token = Manager.get_staff_access_token(company=self.menu.venue.company)

        query_params_dict = {
            "passcode": self.menu.venue.company.passcode
        }

        response = self._get(self.menu_category_id, access_token, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_member_does_not_belong_to_venue(self):
        access_token = Manager.get_company_member_access_token(company=self.menu.venue.company)

        query_params_dict = {
            "passcode": self.menu.venue.company.passcode
        }

        response = self._get(self.menu_category_id, access_token, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_staff_without_passcode(self):
        access_token = Manager.get_staff_access_token(venue=self.menu.venue)

        response = self._get(self.menu_category_id, access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'passcode is required.')

    def test_with_staff_with_incorrect_passcode(self):
        access_token = Manager.get_staff_access_token(venue=self.menu.venue)

        query_params_dict = {
            "passcode": 99999
        }

        response = self._get(self.menu_category_id, access_token, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "Incorrect passcode")

    def test_with_invalid_id(self):
        response = self._get(9999, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(999, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get(999))
