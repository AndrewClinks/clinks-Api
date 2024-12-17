from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class ListDeleteTest(TestCase):
    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.staff = Manager.create_staff()

        company_member = self.staff.company_member

        self.member_access_token = Manager.get_access_token(company_member.user)

    def _delete(self, data, access_token="", **kwargs):
        response = super()._delete(f"/staff", access_token, data)

        return response

    def test_with_admin(self):
        data = {
            "venue_id": self.staff.venue.id,
            "company_member_id": self.staff.company_member_id
        }

        response = self._delete(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.staff.refresh_from_db()

        self.assertIsNone(self.staff.company_member.active_venue)

    def test_with_company_member(self):
        data = {
            "venue_id": self.staff.venue.id,
            "company_member_id": self.staff.company_member_id
        }

        response = self._delete(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.staff.refresh_from_db()

        self.assertIsNone(self.staff.company_member.active_venue)

    def test_failure_with_deleting_staff_belongs_to_another_company(self):
        data = {
            "venue_id": self.staff.venue.id,
            "company_member_id": self.staff.company_member_id
        }

        response = self._delete(data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'You cannot delete this staff')

    def test_failure_with_not_matching_venue(self):
        data = {
            "venue_id": Manager.create_venue().id,
            "company_member_id": self.staff.company_member_id
        }

        response = self._delete(data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(response.json["detail"], "Not found.")

        data = {
            "venue_id": Manager.create_venue(company=self.staff.company_member.company).id,
            "company_member_id": self.staff.company_member_id
        }

        response = self._delete(data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(response.json["detail"], "Not found.")

    def test_failure_with_non_existing_id(self):
        data = {
            "venue_id": 9999,
            "company_member_id": 99999
        }

        response = self._delete(data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(response.json["detail"], "Not found.")

        data = {}

        response = self._delete(data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'company_member_id is required.')

        data = {
            "company_member_id":  self.staff.company_member_id
        }

        response = self._delete(data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'venue_id is required.')

    def test_failure_with_customer(self):
        self.permission_denied_test(self._delete({}, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._delete({}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._delete({}))

