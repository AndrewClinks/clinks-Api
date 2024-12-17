from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _get(self, access_token="", **kwargs):
        response = super()._get("/delivery-distances", access_token=access_token)

        return response

    def test_with_admin(self):
        Manager.create_delivery_distances()

        response = self._get(self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["results"])

    def test_with_company_member(self):
        self.permission_denied_test(self._get(Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
