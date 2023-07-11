from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.driver_1 = Manager.create_driver()
        self.driver_2 = Manager.create_driver(Data.valid_driver_data(first_name='xxx'))

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/drivers", query_params_dict, access_token)

        return response

    def test_with_admin_account(self):
        access_token = Manager.get_admin_access_token()

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 2)

        query_params_dict = {
            "search_term": "xxx"
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 1)

        first_result = response.json["results"][0]
        self.assertEqual(first_result["user"]["id"], self.driver_2.user.id)

    def test_failure_with_customer_account(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
