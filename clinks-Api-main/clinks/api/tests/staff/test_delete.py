from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class DeleteTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.staff = Manager.create_staff()

        company_member = self.staff.company_member

        self.member_access_token = Manager.get_access_token(company_member.user)

    def _delete(self, id, access_token="", **kwargs):
        response = super()._delete(f"/staff/{id}", access_token)

        return response

    def test_with_admin(self):
        staff = Manager.create_staff()
        company_member = staff.company_member
        company_member.active_venue = staff.venue
        company_member.save()

        staff_2 = Manager.create_staff(company_member=Manager.create_company_member(company=staff.venue.company), venue=staff.venue)

        response = super()._get(f"/company-members?company_id={staff.venue.company}", access_token=self.admin_access_token)

        self.assertEqual(response.json["results"][1]["user"]["id"], company_member.user_id)
        self.assertEqual(response.json["results"][1]["venues"][0], staff.venue.id)

        self.assertIsNotNone(staff.company_member.active_venue)

        response = self._delete(staff.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        staff.refresh_from_db()

        self.assertIsNone(staff.company_member.active_venue)

        response = super()._get(f"/company-members?company_id={staff.venue.company}",
                                access_token=self.admin_access_token)

        self.assertEqual(response.json["results"][0]["user"]["id"], staff_2.company_member.user_id)
        self.assertEqual(response.json["results"][0]["venues"][0], staff.venue.id)

        self.assertEqual(response.json["results"][1]["user"]["id"], company_member.user_id)
        self.assertEqual(response.json["results"][1]["venues"], [])

    def test_with_company_member(self):
        response = self._delete(self.staff.id, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.staff.refresh_from_db()

        self.assertIsNone(self.staff.company_member.active_venue)

    def test_failure_with_deleting_staff_belongs_to_another_company(self):
        response = self._delete(self.staff.id, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

        staff = Manager.create_staff()

        response = self._delete(staff.id, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_non_existing_id(self):
        response = self._delete(999, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_customer(self):
        self.permission_denied_test(self._delete(999, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._delete(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._delete(999))

