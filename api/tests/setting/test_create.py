from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...setting.models import Setting

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _post(self, data, access_token="", **kwargs):

        response = super()._post("/settings", data, access_token)

        return response

    def test_add(self):
        data = Data.valid_setting_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["key"], data["key"])
        self.assertEqual(response.json["value"], data["value"])

    def test_update(self):
        self.assertIsNotNone(Setting.get_minimum_age())

        data = Data.valid_setting_data(Constants.SETTING_KEY_MINIMUM_AGE, "21")

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["key"], data["key"])
        self.assertEqual(response.json["value"], data["value"])

        data = Data.valid_setting_data(Constants.SETTING_KEY_MINIMUM_AGE.upper(), "22")

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["key"], data["key"].lower())
        self.assertEqual(response.json["value"], data["value"])

    def test_failure_with_non_integer_value_for_integer_value(self):
        data = Data.valid_setting_data(value="ds")

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Setting"][0], 'value has to be an integer')

        data = Data.valid_setting_data(value="10.9")

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Setting"][0], 'value has to be an integer')

    def test_failure_with_under_18_for_minimum_age_limit(self):
        data = Data.valid_setting_data(Constants.SETTING_KEY_MINIMUM_AGE, 17)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Setting"][0], 'Minimum age cannot be less than 18')

    def test_failure_with_negative_number_for_minimum_order_amount(self):
        data = Data.valid_setting_data(Constants.SETTING_KEY_MINIMUM_ORDER_AMOUNT, -17)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Setting"][0], 'Minimum order amount cannot be less than 50 cents')

    def test_failure_with_less_than_50_cents_for_minimum_order_amount(self):
        data = Data.valid_setting_data(Constants.SETTING_KEY_MINIMUM_ORDER_AMOUNT, -17)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Setting"][0], 'Minimum order amount cannot be less than 50 cents')

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._post({}, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.permission_denied_test(self._post({}))
