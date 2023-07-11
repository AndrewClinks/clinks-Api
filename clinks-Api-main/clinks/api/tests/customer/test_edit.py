import uuid

from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...customer.models import Customer

from ...utils import DateUtils, Constants

from ..utils import Data, Manager


class EditTest(TestCase):

    client = APIClient()

    def setUp(self):
        customer_data = Data.valid_customer_data(email=Data.TEST_EMAIL)

        self.email = customer_data["user"]["email"]
        self.password = customer_data["user"]["password"]

        self.customer = Manager.create_customer(customer_data)
        self.customer_access_token = Manager.get_access_token(self.customer.user)

    def _patch(self, id, data, access_token="", **kwargs):

        response = super()._patch(f"/customers/{id}", data, access_token)

        return response

    def test_success(self):
        updated_data = {
            "user": {
                "first_name": "aaaabb",
                "date_of_birth": DateUtils.format(DateUtils.yesterday(), "%Y-%m-%d"),
                "phone_country_code": "+353",
                "phone_number": "123123123"
            }
        }

        response = self._patch(self.customer.user.id, updated_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["first_name"], updated_data["user"]["first_name"])
        self.assertNotEqual(response.json["user"]["date_of_birth"], updated_data["user"]["date_of_birth"])
        self.assertEqual(response.json["user"]["phone_country_code"], updated_data["user"]["phone_country_code"])
        self.assertEqual(response.json["user"]["phone_number"], updated_data["user"]["phone_number"])

        updated_data = {
            "user": {
                "email": "a@b.cc",
                "current_password": self.password
            }
        }
        response = self._patch(self.customer.user.id, updated_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["email"], updated_data["user"]["email"])

    def test_failure_with_updating_email(self):
        updated_data = {
            "user": {
                "email": "a@b.ccd",
                "current_password": "123445"
            }
        }

        response = self._patch(self.customer.user.id, updated_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json[0], 'Your current password is incorrect')

        updated_data = {
            "user": {
                "email": "a@b.ccd",
            }
        }

        response = self._patch(self.customer.user.id, updated_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["non_field_errors"][0], 'Please include current_password in order to update your email')

    def test_with_identification(self):
        from ...setting.models import Setting
        Setting.update(Constants.SETTING_KEY_MINIMUM_AGE, 22)

        _20_years_ago = DateUtils.years_before(20)

        data = {
            "identification": Data.valid_identification_data()
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        identification = Customer.objects.get(user_id=response.json["user"]["id"]).identification

        self.assertIsNotNone(identification)

        identification_data = Data.valid_identification_data(type=Constants.IDENTIFICATION_TYPE_PASSPORT)
        del identification_data["back"]

        data = {
            "identification": identification_data
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        identification = Customer.objects.get(user_id=response.json["user"]["id"]).identification

        self.assertIsNotNone(identification)

    def test_failure_to_provide_identification_when_age_less_than_minimum_age(self):
        from ...setting.models import Setting
        Setting.update(Constants.SETTING_KEY_MINIMUM_AGE, 22)

        _20_years_ago = DateUtils.years_before(20)
        self.customer.user.date_of_birth = _20_years_ago
        self.customer.user.save()

        data = {
            "user": {
                "first_name": "A"
            }
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            "identification": Data.valid_identification_data()
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            "identification": None
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["identification"][0], 'This field may not be null.')

    def test_failure_with_using_identification_belongs_to_someone_else(self):
        customer = Manager.create_customer(with_identification=True)

        data = {
            "identification": Data.valid_identification_data(customer.identification.front,
                                                                customer.identification.back)
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["identification"]["front"][0], 'This field must be unique.')
        self.assertEqual(response.json["identification"]["back"][0], 'This field must be unique.')

    def test_failure_with_invalid_identification_data(self):
        data = {
            "identification": {}
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["identification"]["type"][0], 'This field is required.')
        self.assertEqual(response.json["identification"]["front"][0], 'This field is required.')

        data = {
            "identification": {
                "type": Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE,
                "front": Manager.create_image().id
            }
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["identification"]["Identification"][0], 'You have to upload back of this identification')

    def test_update_address(self):
        data = {
            "address": Data.valid_address_data()
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["address"])

        address = response.json["address"]

        self.assertEqual(address["latitude"], data["address"]["latitude"])
        self.assertEqual(address["longitude"], data["address"]["longitude"])
        self.assertEqual(address["line_1"], data["address"]["line_1"])
        self.assertEqual(address["line_2"], data["address"]["line_2"])
        self.assertEqual(address["line_3"], data["address"]["line_3"])
        self.assertEqual(address["city"], data["address"]["city"])
        self.assertEqual(address["country"], data["address"]["country"])
        self.assertEqual(address["state"], data["address"]["state"])
        self.assertEqual(address["postal_code"], data["address"]["postal_code"])
        self.assertEqual(address["country_short"], data["address"]["country_short"])

    def test_with_account_belongs_to_someone_else(self):
        customer = Manager.create_customer()

        updated_data = {
            "user": {
                "first_name": "aaaabb"
            }
        }

        response = self._patch(customer.user.id, updated_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["first_name"], updated_data["user"]["first_name"])

        student = Customer.objects.get(user__id=customer.user.id)

        self.assertNotEqual(student.user.first_name, updated_data["user"]["first_name"])

    def test_failure_with_editing_phone_number(self):
        updated_data = {
            "user": {
                "phone_number": "123123123"
            }
        }

        response = self._patch(self.customer.user.id, updated_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["User"][0], "'phone_number' or 'phone_country_code' cannot be null if one of them is provided")

        updated_data = {
            "user": {
                "phone_country_code": "123123123"
            }
        }

        response = self._patch(self.customer.user.id, updated_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["User"][0],
                         "'phone_number' or 'phone_country_code' cannot be null if one of them is provided")

    def test_failure_with_address_without_required_info(self):
        data = {
            "address": {}
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["address"]["latitude"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["longitude"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["line_1"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["city"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["country"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["state"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["country_short"][0], 'This field is required.')

        data = {
            "address": None
        }

        response = self._patch(self.customer.user.id, data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["address"][0], "This field may not be null.")

    def test_failure_with_admin_account(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_admin_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))

