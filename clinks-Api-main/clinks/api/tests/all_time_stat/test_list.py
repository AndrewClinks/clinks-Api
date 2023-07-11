from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...utils import Constants
from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/all-time-stats", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        query_params_dict = {
            "types": f"{Constants.ALL_TIME_STAT_TYPE_SALES_COUNT}, {Constants.ALL_TIME_STAT_TYPE_COMPANY_COUNT}"
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["sales_count"], 0)
        self.assertEqual(response.json["company_count"], 0)

        Manager.create_company()

        query_params_dict = {
            "types": f"{Constants.ALL_TIME_STAT_TYPE_SALES_COUNT}, {Constants.ALL_TIME_STAT_TYPE_COMPANY_COUNT}"
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["sales_count"], 0)
        self.assertEqual(response.json["company_count"], 1)

    def test_with_invalid_query_params(self):
        query_params_dict = {
            "types": f"random"
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue("Invalid value 'random', must be one of " in response.json["detail"])

        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'types is required.')

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(access_token=Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
