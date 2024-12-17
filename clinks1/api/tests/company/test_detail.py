from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...utils import Constants
from ..utils import Manager


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.company = Manager.create_company()

        self.member = self.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

    def _get(self, id, access_token="", query_params_dict=None, **kwargs):
        response = super()._get(f"/companies/{id}", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        response = self._get(self.company.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["title"])
        self.assertIsNotNone(response.json["total_earnings"])
        self.assertIsNotNone(response.json["sales_count"])
        self.assertIsNotNone(response.json["average_delivery_time"])
        self.assertIsNotNone(response.json["logo"]["id"])
        self.assertIsNotNone(response.json["featured_image"]["id"])
        self.assertFalse(response.json["stripe_connected"])
        self.assertIsNotNone(response.json["venue_count"])

        self.assertIsNotNone(response.json["vat_no"])
        self.assertIsNotNone(response.json["eircode"])
        self.assertIsNotNone(response.json["liquor_license_no"])
        self.assertEqual(response.json["status"], Constants.COMPANY_STATUS_SETUP_NOT_COMPLETED)

        self.assertFalse("passcode" in response.json)

    def test_with_company_member(self):
        response = self._get(self.company.id, self.member_access_token, {"passcode": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["title"])
        self.assertIsNotNone(response.json["total_earnings"])
        self.assertIsNotNone(response.json["sales_count"])
        self.assertIsNotNone(response.json["average_delivery_time"])
        self.assertIsNotNone(response.json["logo"]["id"])
        self.assertIsNotNone(response.json["featured_image"]["id"])
        self.assertFalse(response.json["stripe_connected"])
        self.assertIsNotNone(response.json["venue_count"])

        self.assertFalse("passcode" in response.json)

    def test_with_company_belongs_to_someone_else(self):
        response = self._get(self.company.id, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotEqual(response.json["id"], self.company.id)

    def test_return_passcode(self):
        response = self._get(self.company.id, self.admin_access_token, {"passcode": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["passcode"], self.company.passcode)

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(self.company.id, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(self.company.id, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get(self.company.id))


