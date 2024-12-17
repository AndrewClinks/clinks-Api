import uuid

from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Data, Manager


class AuthTest(TestCase):

    client = APIClient()

    def setUp(self):
        customer_data = Data.valid_customer_data(email=Data.TEST_EMAIL)

        self.email = customer_data["user"]["email"]
        self.password = customer_data["user"]["password"]

        self.customer = Manager.create_customer(customer_data)
        self.customer_access_token = Manager.get_access_token(self.customer.user)

    def test_login(self):
        response = Manager.login(self.email, self.password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("customer" in response.json)
        self.assertTrue("tokens" in response.json)

    def test_login_after_password_change(self):
        new_password = "89032Aa)"

        updated_login_data = {
            "user": {
                "password": new_password,
                "current_password": self.password
            }
        }

        response = super()._patch(f"/customers/{self.customer.user.id}", updated_login_data,
                                  Manager.get_access_token(self.customer.user))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = Manager.login(self.email, new_password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("customer" in response.json)

        self.assertTrue("tokens" in response.json)

    def test_request_verify_email(self):
        response = Manager.request_verify_email(self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_verify_email(self):
        self.assertFalse(self.customer.user.email_verified)

        response = Manager.request_verify_email(self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.customer.refresh_from_db()

        response = Manager.verify_email(self.customer_access_token, self.customer.user.verification_code)

        self.customer.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertTrue(self.customer.user.email_verified)

    def test_failure_request_verify_email(self):
        response = Manager.request_verify_email("")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(response.json["detail"], 'Authentication credentials were not provided.')

    def test_failure_verify_email(self):
        response = Manager.verify_email(self.customer_access_token, None)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'Please provide a verification code')

        response = Manager.verify_email(self.customer_access_token, "1234")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'Invalid verification code')

        response = Manager.verify_email("", "1234")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(response.json["detail"], 'Authentication credentials were not provided.')

        response = super()._post("/user/verify-email", {}, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'Please provide a verification code')

