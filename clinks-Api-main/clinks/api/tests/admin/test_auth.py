import uuid

from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Data, Manager


class AuthTest(TestCase):

    client = APIClient()

    def setUp(self):
        admin_data = Data.valid_admin_data(email=Data.TEST_EMAIL)

        self.email = admin_data["user"]["email"]
        self.password = admin_data["user"]["password"]

        self.admin = Manager.create_admin(admin_data)

    def test_login(self):
        response = Manager.login(self.email, self.password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("admin" in response.json)
        self.assertTrue("tokens" in response.json)

    def test_login_after_password_change(self):
        new_password = "89032Aa)"

        updated_login_data = {
            "user": {
                "password": new_password,
                "current_password": self.password
            }
        }

        response = super()._patch(f"/admins/{self.admin.user.id}", updated_login_data,
                                  Manager.get_access_token(self.admin.user))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = Manager.login(self.email, new_password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("admin" in response.json)

        self.assertTrue("tokens" in response.json)

    def test_login_after_creating_admin_staff_account(self):
        data = Data.valid_admin_data()
        email = data["user"]["email"]
        password = data["user"]["password"]

        super()._post("/admins", data,  Manager.get_access_token(self.admin.user))

        response = Manager.login(email, password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("admin" in response.json)

        self.assertTrue("tokens" in response.json)

    def test_success_with_request_reset_password(self):
        response = Manager.request_reset_password(self.email)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_success_reset_password_flow(self):
        response = Manager.request_reset_password(self.email)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.admin.refresh_from_db()

        password = "X4G0-acx"

        response = Manager.reset_password(self.email, self.admin.user.verification_code, password)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        Manager.login(self.email, password)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_failure_request_reset_password_without_required_data(self):
        response = super()._post("/user/request-reset-password", {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'Please provide an email')

    def test_failure_reset_password_without_required_data(self):
        response = Manager.request_reset_password("nonsense@email.tr")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'This email does not belong to a valid user')

    def test_failure_reset_password_with_wrong_verification_code(self):
        response = Manager.reset_password(self.email, "nonsense", "az5b`0dsA")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'Invalid verification code')

    def test_failure_reset_password_with_invalid_email(self):
        response = Manager.reset_password("nonsense@nonsense.ie", "nonsense", "ZPAF03-sa")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'This email does not belong to a user')

    def test_failure_reset_password_with_invalid_passwords(self):
        verification_code = str(uuid.uuid4())[:5]
        self.admin.user.verification_code = verification_code
        self.admin.user.save()

        password = "12345678"

        response = Manager.reset_password(self.email, verification_code, password)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'This password is too common.')

        password = "abc"

        response = Manager.reset_password(self.email, verification_code, password)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"],
                      'This password is too short. It must contain at least 6 characters.')

        password = "abcdefgh"

        response = Manager.reset_password(self.email, verification_code, password)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'This password is too common.')

        password = "zebrarrr"

        response = Manager.reset_password(self.email, verification_code, password)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'This password must contain at least 1 digit, 0-9.')

        password = "989032321"

        response = Manager.reset_password(self.email, verification_code, password)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"],
                      'This password must contain at least 1 uppercase letter, A-Z.')

        password = "A890321AD"

        response = Manager.reset_password(self.email, verification_code, password)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"],
                      'This password must contain at least 1 lowercase letter, a-z.')

        password = "Aa89032da"

        response = Manager.reset_password(self.email, verification_code, password)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"],
                      'The password must contain at least 1 special character: ()[]{}|~!@#$%^&*_-+=;:,<>./?')

        password = "Aa!89032da"

        response = Manager.reset_password(self.email, verification_code, password)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout(self):
        response = Manager.login(self.email, self.password)

        tokens = response.json["tokens"]
        access_token = "Bearer " + tokens["access"]
        refresh_token = tokens["refresh"]

        response = Manager.user_info(access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        Manager.logout(self.admin.user, access_token, refresh_token)

        response = Manager.user_info(access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            "refresh": refresh_token
        }

        response = super()._post("/user/refresh-token", data, access_token)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(response.json["detail"], "No refresh token found")

    def test_logout_twice(self):
        response = Manager.login(self.email, self.password)

        tokens = response.json["tokens"]
        access_token = "Bearer " + tokens["access"]
        refresh_token = tokens["refresh"]

        response = Manager.user_info(access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = Manager.logout(self.admin.user, access_token, refresh_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = Manager.logout(self.admin.user, access_token, refresh_token)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(response.json["detail"], "No refresh token found")

    def test_login_after_deleted_by_super_admin(self):
        data = Data.valid_admin_data()
        email = data["user"]["email"]
        password = data["user"]["password"]

        response = super()._post("/admins", data,  Manager.get_access_token(self.admin.user))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = super()._delete(f"/admins/{response.json['user']['id']}", Manager.get_access_token(self.admin.user))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = Manager.login(email, password)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], "Your account is no longer active")

    def test_failure_login(self):
        response = Manager.login("nonsense@email.ie", self.password)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'A user with this email and password combination does not exist.')