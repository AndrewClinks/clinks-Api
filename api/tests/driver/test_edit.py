from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...utils import Constants, DateUtils


class EditTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.driver = Manager.create_driver()

        self.driver_with_car = Manager.create_driver(Data.valid_driver_data(with_license=True))

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/drivers/{id}", data, access_token)

        return response

    def test_success(self):
        data = {
            "user":
                {
                    "first_name": "new_first_name",
                    "email": "new@email.ie",
                    "role": "student"
                },
            "role": "staff",
            "last_known_location_updated_at": str(DateUtils.now())
        }

        response = self._patch(self.driver.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["first_name"], data["user"]["first_name"])
        self.assertEqual(response.json["user"]["email"], data["user"]["email"])
        self.assertNotEqual(response.json["user"]["role"], data["user"]["role"])
        self.assertIsNone(response.json["last_known_location"])
        self.assertIsNone(response.json["last_known_location_updated_at"])
        self.assertIsNone(response.json["current_delivery_request"])

    def test_success_with_changing_vehicle_type(self):
        self.assertEqual(self.driver_with_car.vehicle_type, Constants.VEHICLE_TYPE_CAR)

        data = {
            "vehicle_type": Constants.VEHICLE_TYPE_BICYCLE
        }

        response = self._patch(self.driver_with_car.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["vehicle_type"], data["vehicle_type"])

    def test_add_delete_identification(self):
        data = {
            "identification": Data.valid_identification_data(type=Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE)
        }

        response = self._patch(self.driver.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["identification"])

        data = {
            "identification": None
        }

        response = self._patch(self.driver.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(response.json["identification"])

    def test_update_identification(self):
        data = {
            "identification": Data.valid_identification_data(type=Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE)
        }

        response = self._patch(self.driver_with_car.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotEqual(self.driver_with_car.identification.id, response.json["identification"]["id"])

        self.driver_with_car.refresh_from_db()

        data = {
            "identification": Data.valid_identification_data(type=Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE)
        }

        data["identification"]["id"] = self.driver_with_car.identification.id

        response = self._patch(self.driver_with_car.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(self.driver_with_car.identification.id, response.json["identification"]["id"])
        self.assertNotEqual(self.driver_with_car.identification.front.id, response.json["identification"]["front"]["id"])
        self.assertNotEqual(self.driver_with_car.identification.back.id, response.json["identification"]["back"]["id"])

        data = {
            "identification": Data.valid_identification_data(type=Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE)
        }

        data["identification"]["id"] = self.driver_with_car.identification.id

        driver_2 = Manager.create_driver(Data.valid_driver_data(with_license=True))

        response = self._patch(driver_2.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], 'This identification is used by different driver')

    def test_failure_with_changing_vehicle_type(self):
        data = {
            "vehicle_type": Constants.VEHICLE_TYPE_CAR
        }

        response = self._patch(self.driver.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], "'identification' is required")

    def test_failure_with_deleting_required_data_for_vehicle_type(self):
        data = {
            "identification": None,
            "vehicle_registration_no": None
        }

        response = self._patch(self.driver_with_car.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], "'identification' is required")

        data = {
            "vehicle_registration_no": None
        }

        response = self._patch(self.driver_with_car.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], "'vehicle_registration_no' is required")

    def test_failure_with_deleting_required_data(self):
        data = {
            "user": {
                "first_name": None,
                "last_name": None,
                "email": None,
                "phone_country_code": None,
                "phone_number": None
            },
            "ppsn": None,
            "vehicle_type": None,
            "identification": None,
            "vehicle_registration_no": None
        }

        response = self._patch(self.driver_with_car.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["first_name"][0], 'This field may not be null.')
        self.assertEqual(response.json["user"]["last_name"][0], 'This field may not be null.')
        self.assertEqual(response.json["user"]["email"][0], 'This field may not be null.')

        self.assertEqual(response.json["ppsn"][0], 'This field may not be null.')
        self.assertEqual(response.json["vehicle_type"][0], 'This field may not be null.')

    def test_failure_with_incorrect_vehicle_type(self):
        data = Data.valid_driver_data()
        data["vehicle_type"] = "nonsense"

        response = self._patch(self.driver.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["vehicle_type"]["Vehicle Type"], "'Vehicle Type needs to be one of ['car', 'scooter', 'bicycle']'")

    def test_failure_with_incorrect_identification_type(self):
        data = Data.valid_driver_data(with_license=True)
        data["identification"]["type"] = Constants.IDENTIFICATION_TYPE_AGE_CARD

        response = self._patch(self.driver.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], 'Identification type has to be driver_license')

    def test_with_driver_account(self):
        user = self.driver.user
        data = {
            "latitude": 53.3331671,
            "longitude": -6.24394,
            "user": {
                "first_name": "random"
            }
        }
        response = self._patch(user.id, data, Manager.get_access_token(user))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["latitude"], data["latitude"])

        self.assertEqual(response.json["longitude"], data["longitude"])

        self.assertNotEqual(response.json["user"]["first_name"], data["user"]["first_name"])
        self.assertIsNotNone(response.json["last_known_location"])
        self.assertIsNotNone(response.json["last_known_location_updated_at"])

        user = self.driver.user
        data = {
            "latitude": None,
            "longitude": None
        }
        response = self._patch(user.id, data, Manager.get_access_token(user))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["latitude"], data["latitude"])

        self.assertEqual(response.json["longitude"], data["longitude"])

    def test_failure_with_updating_latitude_and_longitude(self):
        user = self.driver.user
        data = {
            "latitude": 53.3331671,
            "longitude": None
        }

        response = self._patch(user.id, data, Manager.get_access_token(user))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], "'latitude' or 'longitude' is null when one of them is provided")

    def test_with_uploading_same_identification_data(self):
        data = {
            "identification": Data.valid_identification_data(type=Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE)
        }

        response = self._patch(self.driver.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["identification"])

        data = response.json

        data = {
            "identification":
                {
                    "id": data["identification"]["id"],
                    "type": data["identification"]["type"],
                    "front": data["identification"]["front"]["id"],
                    "back": data["identification"]["back"]["id"],
                }
        }

        response = self._patch(self.driver.user_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_uploading_same_identification_data_for_different_driver(self):
        data = {
            "identification": Data.valid_identification_data(type=Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE)
        }

        response = self._patch(self.driver.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["identification"])

        data = response.json

        data = {
            "identification":
                {
                    "id": data["identification"]["id"],
                    "type": data["identification"]["type"],
                    "front": data["identification"]["front"]["id"],
                    "back": data["identification"]["back"]["id"],
                }
        }

        driver_2 = Manager.create_driver(Data.valid_driver_data(with_license=True))

        response = self._patch(driver_2.user_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Driver"][0], 'This identification is used by different driver')

        del data["identification"]["id"]

        driver_2 = Manager.create_driver(Data.valid_driver_data(with_license=True))

        response = self._patch(driver_2.user_id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["identification"]["Identification"][0], 'front and back needs to be unique')

    def test_with_driver_editing_account_belongs_to_someone_else(self):
        user = self.driver.user
        driver = Manager.create_driver()

        response = self._patch(driver.user_id, {}, Manager.get_access_token(user))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], user.id)

    def test_failure_with_customer_account(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))
