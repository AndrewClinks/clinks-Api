from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...category.models import Category

from ...utils import Constants


class EditTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.item = Manager.create_item()

    def _get(self, id, access_token="", **kwargs):
        response = super()._get(f"/items/{id}", access_token=access_token)

        return response

    def test_success(self):
        response = self._get(self.item.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["id"], self.item.id)

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(999, Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(999, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get(999))
