from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.driver = Manager.create_driver()

    def _get(self, id, access_token="", **kwargs):
        response = super()._get(f"/drivers/{id}", access_token=access_token)

        return response

    def test_success_with_admin(self):
        response = self._get(self.driver.user.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_success_with_driver(self):
        response = self._get(self.driver.user.id, Manager.get_access_token(self.driver.user))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["total_earnings"], 0)
        self.assertEqual(response.json["order_count"], 0)

    def test_failure_with_staff_getting_someone_else_account_details(self):
        response = self._get(self.driver.user.id, Manager.get_driver_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotEqual(response.json["user"]["id"], self.driver.user.id)

    def test_failure_with_customer_account(self):
        self.permission_denied_test(self._get(999, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized_account(self):
        self.unauthorized_account_test(self._get(999))