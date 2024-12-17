from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.venue = Manager.create_venue()

        self.member = self.venue.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

        self.staff = Manager.create_staff(self.member, self.venue)

        self.staff_2 = Manager.create_staff(venue=self.venue)

        self.staff_3 = Manager.create_staff(Manager.create_company_member(company=self.member.company))

        self.staff_4 = Manager.create_staff()

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/staff", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        query_params_dict = {
            "company_id": self.venue.company.id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        query_params_dict = {
            "venue_id": self.venue.id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        query_params_dict = {
            "venue_id": self.staff_4.venue.id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

    def test_with_company_member(self):
        response = self._get(access_token=self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        query_params_dict = {
            "company_id": self.venue.company.id
        }

        response = self._get(query_params_dict, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        query_params_dict = {
            "venue_id": self.staff_4.venue.id
        }

        response = self._get(query_params_dict, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params_dict = {
            "company_id": self.staff_4.venue.company.id
        }

        response = self._get(query_params_dict, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        results = response.json["results"]

        for result in results:
            self.assertTrue(result["venue"] == self.venue.id or result["venue"] == self.staff_3.venue.id)

    def test_failure_without_required_params(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "'company_id' or 'venue_id' is required")

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
