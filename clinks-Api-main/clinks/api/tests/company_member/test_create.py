from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...company.models import Company

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.company = Manager.create_company()

        self.member = self.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/company-members", data, access_token)

        return response

    def test_with_admin(self):
        data = Data.valid_company_member_data(company=self.company)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(self.company.members.first().role, Constants.COMPANY_MEMBER_ROLE_ADMIN)

        self.company.refresh_from_db()

        self.assertEqual(self.company.members.count(), 2)

        self.assertEqual(self.company.members.last().role, Constants.COMPANY_MEMBER_ROLE_STAFF)

    def test_with_company_member(self):
        data = Data.valid_company_member_data(company=self.company)

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(self.company.members.first().role, Constants.COMPANY_MEMBER_ROLE_ADMIN)

        self.assertEqual(response.json["company"]["id"], self.company.id)

        self.company.refresh_from_db()

        self.assertEqual(self.company.members.count(), 2)

        self.assertEqual(self.company.members.last().role, Constants.COMPANY_MEMBER_ROLE_STAFF)

    def test_with_creating_staff(self):
        venue = Manager.create_venue(self.company)

        self.assertEqual(venue.staff.count(), 0)

        data = Data.valid_company_member_data(company=self.company, venue=venue)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(venue.staff.count(), 1)
        self.assertEqual(venue.staff.first().company_member.user_id, response.json["user"]["id"])

    def test_with_creating_staff_with_company_member(self):
        venue = Manager.create_venue(self.company)

        data = Data.valid_company_member_data(company=self.company, venue=venue)

        response = self._post(data, Manager.get_company_member_access_token(company=self.company))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_failure_with_creating_staff_for_venue_belongs_to_different_company(self):
        venue = Manager.create_venue()

        data = Data.valid_company_member_data(company=self.company, venue=venue)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Staff"][0], "This company member does not belong to this venue's company")

    def test_failure_with_creating_staff_with_invalid_venue_id(self):
        data = Data.valid_company_member_data(company=self.company)
        data["venue"] = 111111

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["venue"][0], 'Invalid pk "111111" - object does not exist.')

    def test_failure_with_creating_staff_with_company_member_does_not_belong_to_company(self):
        venue = Manager.create_venue(self.company)

        data = Data.valid_company_member_data(company=self.company, venue=venue)

        response = self._post(data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Staff"][0], "This company member does not belong to this venue's company")

    def test_failure_without_required(self):
        response = self._post({}, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"][0], 'This field is required.')
        self.assertEqual(response.json["company"][0], 'This field is required.')

        data = {
            "user": {},
            "company": self.company.id
        }

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["phone_number"][0], 'This field is required.')
        self.assertEqual(response.json["user"]["phone_country_code"][0], 'This field is required.')
        self.assertEqual(response.json["user"]["first_name"][0], 'This field is required.')
        self.assertEqual(response.json["user"]["last_name"][0], 'This field is required.')
        self.assertEqual(response.json["user"]["email"][0], 'This field is required.')
        self.assertEqual(response.json["user"]["password"][0], 'This field is required.')

    def test_failure_with_assigning_to_non_existing_company(self):
        data = Data.valid_company_member_data()
        data["company"] = 9999

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["company"][0], 'Invalid pk "9999" - object does not exist.')

    def test_with_company_belongs_to_someone_else(self):
        data = Data.valid_company_member_data()
        data["company"] = 9999

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["company"]["id"], self.company.id)

    def test_failure_with_used_email(self):
        data = Data.valid_company_member_data(company=self.company)
        data["user"]["email"] = self.member.user.email
        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["email"][0], 'user with this email already exists.')

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._post({}))