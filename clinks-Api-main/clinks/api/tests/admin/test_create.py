from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.super_admin_access_token = Manager.get_admin_access_token()

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/admins", data, access_token)

        return response

    def test_success(self):
        data = Data.valid_admin_data()

        data["role"] = Constants.ADMIN_ROLE_ADMIN

        response = self._post(data, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["user"]["role"], Constants.USER_ROLE_ADMIN)

        self.assertEqual(response.json["role"], Constants.ADMIN_ROLE_STAFF)

    def test_failure_with_same_email(self):
        data = Data.valid_admin_data()

        self._post(data, self.super_admin_access_token)

        response = self._post(data, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["email"][0], 'user with this email already exists.')

    def test_failure_without_required_data(self):
        response = self._post({}, self.super_admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"][0], "This field is required.")

    def test_failure_with_staff_admin(self):
        staff_admin_access_token = Manager.get_admin_access_token(is_super_admin=False)

        self.permission_denied_test(self._post({}, staff_admin_access_token))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized_account(self):
        self.unauthorized_account_test(self._post({}, ""))
