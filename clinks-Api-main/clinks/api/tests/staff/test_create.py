from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.venue = Manager.create_venue()

        self.member = self.venue.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/staff", data, access_token)

        return response

    def test_with_admin(self):
        data = Data.valid_staff_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["company_member"]["user"]["id"], data["company_member"])

        self.assertEqual(response.json["venue"], data["venue"])

    def test_with_company_member(self):
        data = Data.valid_staff_data(self.member, self.venue)

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["company_member"]["user"]["id"], data["company_member"])

        self.assertEqual(response.json["venue"], data["venue"])

        member = Manager.create_company_member(Data.valid_company_member_data(), self.venue.company)

        data = Data.valid_staff_data(member, self.venue)

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["company_member"]["user"]["id"], data["company_member"])

        self.assertEqual(response.json["venue"], data["venue"])

    def test_failure_without_required_data(self):
        response = self._post({}, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["company_member"][0], 'This field is required.')

        self.assertEqual(response.json["venue"][0], 'This field is required.')

    def test_failure_with_member_does_not_belong_to_company(self):
        data = Data.valid_staff_data(company_member=Manager.create_company_member())

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Staff"][0], 'You do not have access to this venue')

        data = Data.valid_staff_data()

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Staff"][0], 'You do not have access to this venue')

    def test_failure_where_member_does_not_belong_to_venue(self):
        data = Data.valid_staff_data(Manager.create_company_member(), self.venue)

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Staff"][0], "This company member does not belong to this venue's company")

    def test_failure_with_invalid_ids(self):
        data = {
            "company_member": 9999,
            "venue": 9999
        }

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["company_member"][0], 'Invalid pk "9999" - object does not exist.')
        self.assertEqual(response.json["venue"][0], 'Invalid pk "9999" - object does not exist.')

    def test_failure_with_duplicate_staff(self):
        data = Data.valid_staff_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["company_member"]["user"]["id"], data["company_member"])

        self.assertEqual(response.json["venue"], data["venue"])

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Staff"][0], 'This company member is added as staff for this venue already')

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._post({}))
