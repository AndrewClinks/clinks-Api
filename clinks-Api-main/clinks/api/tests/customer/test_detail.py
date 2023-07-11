from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Data, Manager


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer = Manager.create_customer()
        self.customer_access_token = Manager.get_access_token(self.customer.user)
        self.customer_id = self.customer.user.id

    def _get(self, id, access_token="", **kwargs):
        response = super()._get(f"/customers/{id}", access_token=access_token)

        return response

    def test_success(self):
        response = self._get(self.customer_id, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], self.customer_id)

    def test_with_account_belongs_to_someone_else(self):
        id = Manager.create_customer().user.id

        response = self._get(id, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], self.customer.user.id)

    def test_success_with_admin_account(self):
        response = self._get(self.customer_id, Manager.get_admin_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["user"]["id"], self.customer_id)

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(self.customer_id, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get(self.customer_id, ""))
