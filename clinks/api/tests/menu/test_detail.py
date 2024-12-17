from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.venue = Manager.create_venue()

    def _get(self, id, access_token="", query_params_dict=None, **kwargs):
        response = super()._get(f"/menus/{id}", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        response = self._get(self.venue.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["menu_categories"], [])

        Manager.setup_menu(self.venue)

        response = self._get(self.venue.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        menu_categories = response.json["menu_categories"]

        self.assertEqual(len(menu_categories), 1)

        menu_items = menu_categories[0]["menu_items"]

        self.assertEqual(len(menu_items), 1)

        menu_item = menu_items[0]

        self.assertEqual(menu_item["item"]["subcategory"]["parent"], menu_categories[0]["category"]["id"])

        self.assertEqual(menu_categories[0]["order"], 0)

        self.assertEqual(menu_item["order"], 0)

    def test_with_staff_belongs_to_venue(self):
        access_token = Manager.get_staff_access_token(self.venue)

        query_params_dict = {
            "passcode": self.venue.company.passcode
        }

        response = self._get(self.venue.id, access_token, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["menu_categories"], [])

    def test_failure_with_staff_without_passcode(self):
        access_token = Manager.get_staff_access_token(self.venue)

        response = self._get(self.venue.id, access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'passcode is required.')

    def test_with_staff_with_incorrect_passcode(self):
        access_token = Manager.get_staff_access_token(self.venue)

        query_params_dict = {
            "passcode": 99999
        }

        response = self._get(self.venue.id, access_token, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "Incorrect passcode")

    def test_failure_with_member_belongs_to_different_company(self):
        response = self._get(self.venue.id, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_member_belongs_to_same_company_but_not_in_venue_staff(self):
        member_access_token = Manager.get_company_member_access_token(company=self.venue.company)

        query_params_dict = {
            "passcode": self.venue.company.passcode
        }

        response = self._get(self.venue.id, member_access_token, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_staff_not_in_venue_staff(self):
        access_token = Manager.get_staff_access_token(company=self.venue.company)

        query_params_dict = {
            "passcode": self.venue.company.passcode
        }

        response = self._get(self.venue.id, access_token, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_id_does_not_exist(self):
        response = self._get(99999)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_with_customer(self):
        response = self._get(self.venue.id, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["menu_categories"], [])

    def test_with_driver(self):
        response = self._get(self.venue.id, Manager.get_driver_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["menu_categories"], [])

    def test_failure_with_unauthorized(self):
        response = self._get(self.venue.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["menu_categories"], [])



