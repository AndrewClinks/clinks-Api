from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Data, Manager


class GetTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer_1 = Manager.create_customer()
        self.customer_access_token = Manager.get_access_token(self.customer_1.user)
        self.customer_id = self.customer_1.user.id

        self.customer_2 = Manager.create_customer(Data.valid_customer_data(first_name="xxx"))

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/customers", query_params_dict, access_token)

        return response

    def test_with_admin_account(self):
        access_token = Manager.get_admin_access_token()

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 2)

        query_params_dict = {
            "search_term": "Xxx"
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 1)

        first_result = response.json["results"][0]
        self.assertEqual(first_result["user"]["id"], self.customer_2.user.id)
        self.assertEqual(first_result["order_count"], 0)
        self.assertIsNone(first_result["last_order_at"])

    def test_failure_with_customer_account(self):
        response = self._get(access_token=self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'You do not have permission to access this')

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.permission_denied_test(self._get())
