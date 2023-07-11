from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.super_admin = Manager.create_admin()

        self.super_admin_access_token = Manager.get_access_token(self.super_admin.user)

        self.staff_admin = Manager.create_admin(is_super_admin=False)

        self.staff_admin_access_token = Manager.get_access_token(self.staff_admin.user)

    def _get(self, access_token="", **kwargs):
        response = super()._get("/admins", access_token=access_token)

        return response

    def test_success_with_super_admin(self):
        response = self._get(self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 2)

    def test_success_with_staff_admin(self):
        response = self._get(self.staff_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 2)

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(Manager.get_driver_access_token()))

    def test_failure_with_unauthorized_account(self):
        self.unauthorized_account_test(self._get())
