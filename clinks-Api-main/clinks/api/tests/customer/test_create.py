from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...customer.models import Customer
from ...all_time_stat.models import AllTimeStat

from ...utils import Constants, DateUtils

from ..utils import Data, Manager


class CreateTest(TestCase):

    client = APIClient()

    def _post(self, data, **kwargs):
        response = super()._post("/customers", data)

        return response

    def test_success(self):
        data = Data.valid_customer_data()

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["customer"]["user"]["role"], Constants.USER_ROLE_CUSTOMER)

        self.assertIsNotNone(response.json["tokens"])
        self.assertIsNotNone(response.json["tokens"]["access"])
        self.assertIsNotNone(response.json["tokens"]["refresh"])
        self.assertIsNone(response.json["customer"]["address"])

        count = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_CUSTOMER_COUNT)

        self.assertEqual(count, 1)

    def test_failure_invalid_date_of_birth(self):
        data = Data.valid_customer_data()

        del data["user"]["date_of_birth"]

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["date_of_birth"][0], 'This field is required.')

        data["user"]["date_of_birth"] = "2100-01-01"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["date_of_birth"][0], 'You need to be at least 18 years old to use this app.')

        data["user"]["date_of_birth"] = DateUtils.format(DateUtils.yesterday(), "%Y-%m-%d")

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["date_of_birth"][0],
                         'You need to be at least 18 years old to use this app.')

    def test_failure_without_email(self):
        data = Data.valid_customer_data()

        del data["user"]["email"]

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["email"][0], 'This field is required.')

    def test_failure_without_duplicate_email(self):
        customer = Manager.create_customer()

        data = Data.valid_customer_data()

        data["user"]["email"] = customer.user.email

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["email"][0], 'user with this email already exists.')

    def test_failure_with_invalid_passwords(self):
        data = Data.valid_customer_data()
        data["user"]["password"] = "12345678"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["password"][0], 'This password is too common.')

        data["user"]["password"] = "abc"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["password"][0], 'This password is too short. It must contain at least 6 characters.')

        data["user"]["password"] = "abcdefgh"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["password"][0], 'This password is too common.')

        data["user"]["password"] = "zebrarrr"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["password"][0], 'This password must contain at least 1 digit, 0-9.')

        data["user"]["password"] = "989032321"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["password"][0], 'This password must contain at least 1 uppercase letter, A-Z.')

        data["user"]["password"] = "A890321AD"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["password"][0],
                         'This password must contain at least 1 lowercase letter, a-z.')

        data["user"]["password"] = "Aa89032da"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["password"][0],
                         'The password must contain at least 1 special character: ()[]{}|~!@#$%^&*_-+=;:,<>./?')

        data["user"]["password"] = "Aa!89032da"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_failure_with_adding_phone_number(self):
        data = Data.valid_customer_data()
        data["user"]["phone_number"] = "123123123"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["User"][0],
                         "'phone_number' or 'phone_country_code' cannot be null if one of them is provided")

        del data["user"]["phone_number"]
        data["user"]["phone_country_code"] = "123123123"

        response = self._post(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["User"][0],
                         "'phone_number' or 'phone_country_code' cannot be null if one of them is provided")


