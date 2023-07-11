from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager


class DeleteTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.super_admin = Manager.create_admin()

        self.super_admin_access_token = Manager.get_access_token(self.super_admin.user)

    def _delete(self, id, access_token="", **kwargs):
        response = super()._delete(f"/admins/{id}", access_token)

        return response

    def test_success(self):
        admin = Manager.create_admin(is_super_admin=False)

        response = self._delete(admin.user.id, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_failure_with_wrong_id(self):
        response = self._delete(999, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_deleting_own_account(self):
        response = self._delete(self.super_admin.user.id, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "You cannot delete this account")

    def test_failure_with_staff(self):
        self.permission_denied_test(self._delete(999, Manager.get_admin_staff_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._delete(999, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._delete(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized_account(self):
        self.unauthorized_account_test(self._delete(999, ""))
