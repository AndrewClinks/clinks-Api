from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase
from ...all_time_stat.models import AllTimeStat

from ..utils import Data, Manager

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/drivers", data, access_token)

        return response

    def test_success_without_license(self):
        driver_count = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DRIVER_COUNT)

        data = Data.valid_driver_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json["user"]["role"], Constants.USER_ROLE_DRIVER)
        self.assertEqual(response.json["vehicle_type"], data["vehicle_type"])
        self.assertEqual(response.json["order_count"], 0)
        self.assertEqual(response.json["total_earnings"], 0)
        self.assertEqual(response.json["average_delivery_time"], 0)
        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DRIVER_COUNT), driver_count + 1)

        driver_count = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DRIVER_COUNT)

        data = Data.valid_driver_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DRIVER_COUNT), driver_count + 1)

    def test_success_with_license(self):
        data = Data.valid_driver_data(with_license=True)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["user"]["role"], Constants.USER_ROLE_DRIVER)
        self.assertEqual(response.json["vehicle_type"], data["vehicle_type"])
        self.assertIsNotNone(response.json["identification"])
        self.assertEqual(response.json["identification"]["type"], Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE)
        self.assertEqual(response.json["order_count"], 0)
        self.assertEqual(response.json["total_earnings"], 0)
        self.assertEqual(response.json["average_delivery_time"], 0)

    def test_failure_without_required_data(self):
        response = self._post({}, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"][0], "This field is required.")
        self.assertEqual(response.json["ppsn"][0], "This field is required.")
        self.assertEqual(response.json["vehicle_type"][0], "This field is required.")

        data = {
            "user": {},
            "vehicle_type": Constants.VEHICLE_TYPE_CAR
        }

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["phone_number"][0], "This field is required.")
        self.assertEqual(response.json["user"]["phone_number"][0], "This field is required.")

        data = Data.valid_driver_data()
        data["vehicle_type"] = Constants.VEHICLE_TYPE_CAR

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], "'identification' is required")

        data["identification"] = Data.valid_identification_data(type=Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], "'vehicle_registration_no' is required")

    def test_failure_with_incorrect_vehicle_type(self):
        data = Data.valid_driver_data()
        data["vehicle_type"] = "nonsense"

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["vehicle_type"]["Vehicle Type"], "'Vehicle Type needs to be one of ['car', 'scooter', 'bicycle']'")

    def test_failure_with_incorrect_identification_type(self):
        data = Data.valid_driver_data(with_license=True)
        data["identification"]["type"] = Constants.IDENTIFICATION_TYPE_AGE_CARD

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], 'Identification type has to be driver_license')

    def test_failure_with_customer_account(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_driver_account(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._post({}))
