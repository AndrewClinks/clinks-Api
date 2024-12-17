from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...company.models import Company

from ...utils import Constants


class EditTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.company = Manager.create_company()

        self.member = self.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/company-members/{id}", data, access_token)

        return response

    def test_with_admin(self):
        new_password = "90Scx-ab"

        data = {
            "user": {
                "password": new_password
            }
        }

        response = self._patch(self.member.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = Manager.login(self.member.user.email, new_password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_with_current_user(self):
        data = {
            "user": {
                "first_name": "new_first_name"
            },
            "company": 2
        }

        response = self._patch(self.member.user.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json["user"]["first_name"], data["user"]["first_name"])
        self.assertNotEqual(response.json["company"]["id"], data["company"])

    def test_with_active_venue(self):
        staff = Manager.create_staff(self.member)

        data = {
            "active_venue": staff.venue.id
        }

        response = self._patch(self.member.user.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["active_venue"], staff.venue.id)

        staff = Manager.create_staff(venue=staff.venue)

        data = {
            "active_venue": staff.venue.id
        }

        response = self._patch(self.member.user.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["active_venue"], staff.venue.id)

    def test_failure_with_active_venue_belongs_to_another_company(self):
        data = {
            "active_venue": Manager.create_venue().id
        }

        response = self._patch(self.member.user.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["CompanyMember"][0], 'This venue does not belong to your company.')

    def test_failure_with_active_venue_where_current_not_in_staff(self):
        data = {
            "active_venue": Manager.create_venue(company=self.member.company).id
        }

        response = self._patch(self.member.user.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["CompanyMember"][0], "You aren't in staff list for this venue.")

    def test_failure_with_active_invalid_venue_id(self):
        data = {
            "active_venue": 999
        }

        response = self._patch(self.member.user.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["active_venue"][0], 'Invalid pk "999" - object does not exist.')

    def test_with_account_belongs_to_someone_else(self):
        member = Manager.create_company_member()

        response = self._patch(member.user.id, {}, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], "An object with this id does not exist")

    def test_failure_with_setting_required_info_to_none(self):
        data = {
            "user": {
                "first_name": None,
                "last_name": None,
                "email": None,
                "phone_country_code": None,
                "phone_number": None
            },
            "company": None
        }

        response = self._patch(self.member.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["user"]["phone_number"][0], 'This field may not be null.')
        self.assertEqual(response.json["user"]["phone_country_code"][0], 'This field may not be null.')
        self.assertEqual(response.json["user"]["first_name"][0], 'This field may not be null.')
        self.assertEqual(response.json["user"]["last_name"][0], 'This field may not be null.')
        self.assertEqual(response.json["user"]["email"][0], 'This field may not be null.')

    def test_failure_with_changing_assigned_company(self):
        data = {
            "company": 2
        }

        response = self._patch(self.member.user.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotEqual(response.json["company"]["id"], data["company"])

    def test_failure_with_customer(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))