import uuid

from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Data, Manager


class AuthTest(TestCase):

    client = APIClient()

    def setUp(self):
        driver_data = Data.valid_driver_data(email=Data.TEST_EMAIL)

        self.email = driver_data["user"]["email"]
        self.password = driver_data["user"]["password"]

        self.driver = Manager.create_driver(driver_data)

    def test_login(self):
        response = Manager.login(self.email, self.password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("driver" in response.json)
        self.assertTrue("tokens" in response.json)
        self.assertIsNone(response.json["driver"]["current_delivery_request"])

        self.assertEqual(response.json["driver"]["total_earnings"], 0)
        self.assertEqual(response.json["driver"]["order_count"], 0)

    def test_login_after_password_change(self):
        new_password = "89032Aa)"

        updated_login_data = {
            "user": {
                "password": new_password
            }
        }

        response = super()._patch(f"/drivers/{self.driver.user.id}", updated_login_data,
                                  Manager.get_admin_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = Manager.login(self.email, new_password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("driver" in response.json)

        self.assertTrue("tokens" in response.json)

    def test_failure_to_login_after_deleted_by_admin(self):
        response = super()._delete(f"/drivers/{self.driver.user.id}",
                                  Manager.get_admin_access_token())

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = Manager.login(self.email, self.password)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'Your account is no longer active')