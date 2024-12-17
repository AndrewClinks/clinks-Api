from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase
from ...all_time_stat.models import AllTimeStat

from ..utils import Data, Manager

from ...company.models import Company

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/companies", data, access_token)

        return response

    def test_success(self):
        company_count = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_COMPANY_COUNT)
        data = Data.valid_company_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue("original" in response.json["logo"])
        self.assertTrue("original" in response.json["featured_image"])
        self.assertEqual(response.json["total_earnings"], 0)
        self.assertEqual(response.json["sales_count"], 0)
        self.assertEqual(response.json["average_delivery_time"], 0)
        self.assertEqual(response.json["venue_count"], 0)
        self.assertFalse(response.json["stripe_connected"])

        members = Company.objects.get(id=response.json["id"]).members

        self.assertEqual(members.count(), 1)

        first_member = members.first()

        self.assertEqual(first_member.role, Constants.COMPANY_MEMBER_ROLE_ADMIN)
        self.assertEqual(first_member.user.role, Constants.USER_ROLE_COMPANY_MEMBER)
        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_COMPANY_COUNT), company_count+1)

    def test_check_if_passcode_unique(self):
        response = self._post(Data.valid_company_data(), self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        passcode = Company.objects.get(id=response.json["id"]).passcode

        response = self._post(Data.valid_company_data(), self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertNotEqual(passcode, Company.objects.get(id=response.json["id"]).passcode)

    def test_with_multiple_members(self):
        data = Data.valid_company_data()
        members = [
            Data.valid_company_member_data(),
            Data.valid_company_member_data()
        ]

        data["members"] = members
        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        members = Company.objects.get(id=response.json["id"]).members

        self.assertEqual(members.count(), 2)

        first_member = members.first()
        second_member = members.last()

        self.assertEqual(first_member.role, Constants.COMPANY_MEMBER_ROLE_ADMIN)
        self.assertEqual(first_member.user.role, Constants.USER_ROLE_COMPANY_MEMBER)

        self.assertEqual(second_member.role, Constants.COMPANY_MEMBER_ROLE_STAFF)
        self.assertEqual(second_member.user.role, Constants.USER_ROLE_COMPANY_MEMBER)

    def test_failure_without_required_data(self):
        response = self._post({}, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["title"][0], 'This field is required.')
        self.assertEqual(response.json["eircode"][0], 'This field is required.')
        self.assertEqual(response.json["vat_no"][0], 'This field is required.')
        self.assertEqual(response.json["members"][0], 'This field is required.')

        data = Data.valid_company_data()
        data["members"] = []

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["members"]["non_field_errors"][0], 'This list may not be empty.')

        data["members"] = {}

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["members"]["non_field_errors"][0], 'Expected a list of items but got type "dict".')

        data["members"] = [{}]

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["members"][0]["user"][0], 'This field is required.')

    def test_failure_with_using_logo_belongs_to_different_company(self):
        company = Manager.create_company()

        data = Data.valid_company_data()
        data["logo"] = company.logo.id
        data["featured_image"] = company.featured_image.id

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["featured_image"][0], 'This field must be unique.')

        self.assertEqual(response.json["logo"][0], 'This field must be unique.')

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._post({}, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._post({}))
