from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager


class GetTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.super_admin = Manager.create_admin()

        self.super_admin_access_token = Manager.get_access_token(self.super_admin.user)

        self.staff_admin = Manager.create_admin(is_super_admin=False)

    def _get(self, id, access_token="", **kwargs):
        response = super()._get(f"/admins/{id}", access_token=access_token)

        return response

    def test_success(self):
        response = self._get(self.staff_admin.user.id, Manager.get_access_token(self.staff_admin.user))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], self.staff_admin.user.id)

        response = self._get(self.super_admin.user.id, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], self.super_admin.user.id)

    def test_with_admin_getting_staff_account(self):
        response = self._get(self.staff_admin.user.id, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], self.staff_admin.user.id)

    def test_failure_with_staff_getting_someone_else_account_details(self):
        response = self._get(self.super_admin.user.id, Manager.get_access_token(self.staff_admin.user))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], self.staff_admin.user.id)

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(111, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(111, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized_account(self):
        self.unauthorized_account_test(self._get(111))
