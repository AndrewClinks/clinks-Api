from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.company = Manager.create_company()

        self.member = self.company.members.first()

        self.company_venue = Manager.create_venue(self.member.company)

        self.company_2 = Manager.create_company(Data.valid_company_data("bunsen"))

        self.company_2_staff = Manager.create_staff(Manager.create_company_member(company=self.company_2))

        self.company_3 = Manager.create_company()

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/companies", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        self.assertIsNotNone(results[0]["title"])
        self.assertIsNotNone(results[0]["total_earnings"])
        self.assertIsNotNone(results[0]["logo"]["id"])
        self.assertIsNotNone(results[0]["featured_image"]["id"])
        self.assertEqual(results[0]["venues"], [])
        self.assertEqual(results[0]["id"], self.company_3.id)

        self.assertEqual(results[1]["venues"][0]["id"], self.company_2_staff.venue.id)
        self.assertIsNotNone(results[1]["venues"][0]["staff"])

        self.assertIsNotNone(results[1]["venues"][0]["staff"][0]["company_member"]["user"]["id"],
                             self.company_2_staff.company_member.user_id)
        self.assertIsNotNone(results[1]["venues"][0]["staff"][0]["venue"], self.company_2_staff.venue.id)
        self.assertEqual(results[1]["id"], self.company_2.id)

        self.assertEqual(results[2]["id"], self.company.id)
        self.assertEqual(results[2]["venues"][0]["id"], self.company_venue.id)
        self.assertEqual(results[2]["venues"][0]["staff"], [])

        query_params_dict = {
            "search_term": self.company_2.title
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.company_2.id)

        query_params_dict = {
            "search_term": self.member.user.email
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.company.id)

    def test_with_company_member(self):
        self.permission_denied_test(self._get(access_token=Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
