from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from freezegun import freeze_time

from ...availability.models import Availability

from ...utils import Constants

from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer_access_token = Manager.get_customer_access_token()

    def _get(self, access_token="", **kwargs):
        response = super()._get("/status", access_token=access_token)

        return response

    def test_success(self):
        with freeze_time("2022-01-01 12:00:01"):
            response = self._get(self.customer_access_token)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertTrue(response.json["available"])

        with freeze_time("2022-01-02 21:00:01"):
            response = self._get(self.customer_access_token)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertTrue(response.json["available"])

    def test_with_special_days(self):
        with freeze_time("2021-03-17 12:31:01"):
            response = self._get(self.customer_access_token)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.json["available"])

        with freeze_time("2021-03-17 12:29:01"):
            response = self._get(self.customer_access_token)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.json["available"])

        with freeze_time("2021-03-17 20:00:01"):
            response = self._get(self.customer_access_token)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.json["available"])

        with freeze_time("2021-03-17 21:31:01"):
            response = self._get(self.customer_access_token)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.json["available"])

    def test_with_closed_days(self):
        with freeze_time("2021-12-25 12:31:01"):
            response = self._get(self.customer_access_token)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.json["available"])

        availability = Availability.objects.get(day=Constants.DAY_FRIDAY)

        availability.closed = True
        availability.save()

        with freeze_time("2022-12-25 12:31:01"):
            response = self._get(Manager.get_customer_access_token())
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.json["available"])

    def test_with_timezones(self):
        with freeze_time("2022-01-01 10:30:01"):
            response = self._get()

        self.assertTrue(response.json["available"])

        with freeze_time("2022-01-01 09:30:01"):
            response = self._get()

        self.assertFalse(response.json["available"])

        with freeze_time("2022-04-04 09:30:01"):
            response = self._get()

        self.assertTrue(response.json["available"])

        with freeze_time("2022-01-01 20:31:01"):
            response = self._get()

        self.assertTrue(response.json["available"])

        with freeze_time("2022-04-04 20:31:01"):
            response = self._get()

        self.assertFalse(response.json["available"])

        with freeze_time("2022-04-04 20:29:01"):
            response = self._get()

        self.assertTrue(response.json["available"])

    def test_with_unauthorized(self):
        response = self._get()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_admin(self):
        self.permission_denied_test(self._get(access_token=Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(access_token=Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))


