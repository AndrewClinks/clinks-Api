from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.company = Manager.create_company()

        self.member = self.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

    def _get(self, id, access_token="", **kwargs):
        response = super()._get(f"/company-members/{id}", access_token=access_token)

        return response

    def test_with_admin(self):
        response = self._get(self.member.user_id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["user"]["id"])
        self.assertIsNotNone(response.json["company"]["id"])

    def test_with_current_user(self):
        response = self._get(self.member.user_id, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["user"]["id"])
        self.assertIsNotNone(response.json["company"]["id"])

    def test_with_account_belongs_to_someone_else(self):
        member = Manager.create_company_member(company=self.company)

        response = self._get(member.user_id, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], member.user.id)

        member_2 = Manager.create_company_member()

        response = self._get(member_2.user.id, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(999, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get(999))