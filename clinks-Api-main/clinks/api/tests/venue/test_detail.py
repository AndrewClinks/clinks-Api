from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.venue = Manager.create_venue()

        self.member = self.venue.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

    def _get(self, id, access_token="", **kwargs):
        response = super()._get(f"/venues/{id}", access_token=access_token)

        return response

    def test_with_admin(self):
        response = self._get(self.venue.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["company"])

    def test_with_company_member(self):
        response = self._get(self.venue.id, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_with_customer(self):
        response = self._get(self.venue.id, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_with_unauthorized(self):
        response = self._get(self.venue.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_non_existing_id(self):
        response = self._get(99999)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_company_member_with_venue_belongs_to_someone_else(self):
        venue = Manager.create_venue()
        response = self._get(venue.id, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(999, Manager.get_driver_access_token()))


