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

        self.category = Manager.create_category()

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/categories/{id}", data, access_token)

        return response

    def test_with_admin(self):
        data = {
            "title": "new_title",
            "image": Manager.create_image().id
        }

        response = self._patch(self.category.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["title"], data["title"])
        self.assertEqual(response.json["image"], data["image"])
        self.assertIsNone(response.json["parent"])

        parent = Manager.create_category()

        Manager.create_category(Data.valid_category_data(parent=parent))

        data = {
            "title": data["title"],
            "parent": parent.id
        }

        response = self._patch(self.category.id, data, self.admin_access_token)

        self.assertEqual(response.json["parent"], data["parent"])

        data = {
            "parent": None
        }

        response = self._patch(self.category.id, data, self.admin_access_token)

        self.assertIsNone(response.json["parent"])

    def test_failure_with_null_required_fields(self):
        data = {
            "title": None,
            "image": None
        }

        response = self._patch(self.category.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["title"][0], 'This field may not be null.')
        self.assertEqual(response.json["image"][0], 'This field may not be null.')

    def test_failure_with_adding_parent_to_category_with_subcategories(self):
        category = Manager.create_category()
        subcategory = Manager.create_category(Data.valid_category_data(category))

        data = {
            "parent": Manager.create_category().id
        }

        response = self._patch(category.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Category"][0], 'This category cannot have a parent since it has subcategories')

    def test_failure_with_editing_to_title_that_already_exists(self):
        category = Manager.create_category()

        data = {
            "title": category.title
        }

        response = self._patch(self.category.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Category"][0], 'A category with this title exists already')

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))