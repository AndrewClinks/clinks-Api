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
        response = super()._get("/settings", query_params_dict, access_token)

        return response

    def test_success(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_with_filter(self):
        query_params_dict = {
            "key": Constants.SETTING_KEY_MINIMUM_ORDER_AMOUNT
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 1)

        query_params_dict = {
            "key": Constants.SETTING_KEY_MINIMUM_AGE
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 1)
        self.assertEqual(response.json["results"][0]["key"], Constants.SETTING_KEY_MINIMUM_AGE)

    def test_with_customer(self):
        query_params_dict = {
            "key": Constants.SETTING_KEY_MINIMUM_AGE
        }

        response = self._get(query_params_dict, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 1)
        self.assertEqual(response.json["results"][0]["key"], Constants.SETTING_KEY_MINIMUM_AGE)

    def test_with_unauthorized(self):
        query_params_dict = {
            "key": Constants.SETTING_KEY_MINIMUM_AGE
        }

        response = self._get(query_params_dict, "")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 1)
        self.assertEqual(response.json["results"][0]["key"], Constants.SETTING_KEY_MINIMUM_AGE)

    def test_failure_with_no_filters_with_customer(self):
        response = self._get(access_token=Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "'key' filter is required")

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(access_token=Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))


