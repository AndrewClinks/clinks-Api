from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager


class EditTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.super_admin = Manager.create_admin()

        self.super_admin_access_token = Manager.get_access_token(self.super_admin.user)

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/admins/{id}", data, access_token)

        return response

    def test_success(self):
        data = {
            "user":
                {
                    "first_name": "new_first_name",
                    "email": "new@email.ie",
                    "role": "student"
                },
            "role": "staff"
        }

        response = self._patch(self.super_admin.user.id, data, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["first_name"], data["user"]["first_name"])
        self.assertNotEqual(response.json["user"]["email"], data["user"]["email"])
        self.assertNotEqual(response.json["user"]["role"], data["user"]["role"])
        self.assertNotEqual(response.json["role"], data["role"])

    def test_super_admin_editing_staff_account(self):
        staff_admin = Manager.create_admin(is_super_admin=False)
        new_email = "new@email.ie"
        new_password = "E3^xyzf"

        data = {
            "user":
                {
                    "first_name": "new_first_name",
                    "email": new_email,
                    "password": new_password,
                    "role": "student"
                },
            "role": "admin"
        }

        response = self._patch(staff_admin.user.id, data, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], staff_admin.user.id)
        self.assertEqual(response.json["user"]["first_name"], data["user"]["first_name"])
        self.assertEqual(response.json["user"]["email"], data["user"]["email"])
        self.assertNotEqual(response.json["user"]["role"], data["user"]["role"])
        self.assertNotEqual(response.json["role"], data["role"])

        response = Manager.login(new_email, new_password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json["user"]["email"], data["user"]["email"])
        self.assertEqual(response.json["user"]["id"], staff_admin.user.id)

    def test_failure_admin_editing_staff_email_to_already_existing_email(self):
        staff_admin = Manager.create_admin(is_super_admin=False)
        data = {
            "user":
                {
                    "email": self.super_admin.user.email,
                },
        }

        response = self._patch(staff_admin.user.id, data, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["email"][0], 'A user with this email already exists')

    def test_failure_changing_password_invalid_password(self):
        data = {
            "user":
                {
                    "password": "123456",
                },
        }

        response = self._patch(self.super_admin.user.id, data, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["password"][0], "This password is too common.")

    def test_failure_changing_password_without_required_data(self):
        data = {
            "user":
                {
                    "password": "A9SD_+abc",
                },
        }

        response = self._patch(self.super_admin.user.id, data, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json[0], 'Please include current_password in order to update your password')

    def test_failure_staff_editing_another_admin_account(self):
        staff_admin_access_token = Manager.get_admin_staff_access_token()

        response = self._patch(self.super_admin.user.id, {}, staff_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotEqual(response.json["user"]["id"], self.super_admin.user.id)

    def test_failure_super_admin_editing_invalid_account(self):
        response = self._patch(999, {}, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], "An object with this id does not exist")

    def test_failure_with_customer(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized_account(self):
        self.unauthorized_account_test(self._patch(self.super_admin.user.id, {}))