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

        self.member_access_token = Manager.get_access_token(self.member.user)

        company_2 = Manager.create_company(data=Data.valid_company_data(members=[Data.valid_company_member_data("x@y.zz")]))
        self.member_2 = company_2.members.first()

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/company-members", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        staff_1 = Manager.create_staff(self.member)
        staff_2 = Manager.create_staff(self.member)

        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        result_second = results[1]

        self.assertEqual(result_second["user"]["id"], self.member.user_id)
        self.assertEqual(len(result_second["venues"]), 2)
        self.assertEqual(result_second["venues"], [staff_1.venue_id, staff_2.venue_id])

        query_params_dict = {
            "company_id": self.member.company.id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["user"]["id"], self.member.user_id)

        query_params_dict = {
            "search_term": "x@y"
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["user"]["id"], self.member_2.user_id)

    def test_with_company_member(self):
        response = self._get(access_token=self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        Manager.create_company_member(company=self.company)

        response = self._get(access_token=self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        query_params_dict = {
            "search_term": "x@y"
        }

        response = self._get(query_params_dict, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())