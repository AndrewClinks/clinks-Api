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

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/items/{id}", data, access_token)

        return response

    def test_success(self):
        subcategory_old = Category.objects.get(id=self.item.subcategory_id)
        subcategory_old_item_count = subcategory_old.item_count
        category_old_item_count = subcategory_old.parent.item_count

        data = Data.valid_item_data()

        response = self._patch(self.item.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["image"]["id"], data["image"])
        self.assertEqual(response.json["title"], data["title"])
        self.assertEqual(response.json["description"], data["description"])
        self.assertEqual(response.json["sales_count"], 0)
        self.assertEqual(response.json["subcategory"]["id"], data["subcategory"])

        subcategory = Category.objects.get(id=response.json["subcategory"]["id"])
        self.assertEqual(subcategory.item_count, 1)
        self.assertEqual(subcategory.parent.item_count, 1)

        subcategory_old.refresh_from_db()
        self.assertEqual(subcategory_old.item_count, subcategory_old_item_count-1)
        self.assertEqual(subcategory_old.parent.item_count, category_old_item_count-1)

        subcategory_newest = Manager.create_subcategory(parent=subcategory.parent)

        data = {
            "subcategory": subcategory_newest.id
        }

        response = self._patch(self.item.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        subcategory_newest.refresh_from_db()

        self.assertEqual(subcategory_newest.item_count, 1)
        self.assertEqual(subcategory_newest.parent.item_count, 1)

        subcategory.refresh_from_db()

        self.assertEqual(subcategory.item_count, 0)

    def test_failure_with_using_same_title(self):
        item = Manager.create_item()

        data = {
            "title": item.title
        }

        response = self._patch(self.item.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Item"][0], 'An item with this title exists already')

        data = {
            "title": item.title.upper()
        }

        response = self._patch(self.item.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Item"][0], 'An item with this title exists already')

    def test_failure_with_using_category_instead_of_subcategory(self):
        data = {
            "subcategory": Manager.create_category().id
        }

        response = self._patch(self.item.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["subcategory"]["Subcategory"], 'It has to be a subcategory')

    def test_failure_with_invalid_id(self):
        response = self._patch(999, {}, Manager.get_admin_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))