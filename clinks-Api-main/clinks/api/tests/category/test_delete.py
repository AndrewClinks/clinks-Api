from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class DeleteTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _delete(self, id, access_token="", **kwargs):
        response = super()._delete(f"/categories/{id}", access_token)

        return response

    def test_category(self):
        category_1 = Manager.create_category()

        response = self._delete(category_1.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        category_1.refresh_from_db()
        self.assertIsNotNone(category_1.deleted_at)

        category_2 = Manager.create_category()
        subcategory_2 = Manager.create_subcategory(parent=category_2)

        response = self._delete(category_2.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        category_2.refresh_from_db()
        self.assertIsNotNone(category_2.deleted_at)

        subcategory_2.refresh_from_db()
        self.assertIsNotNone(subcategory_2.deleted_at)

        category_3 = Manager.create_category()
        subcategory_3 = Manager.create_subcategory(parent=category_3)
        item_3 = Manager.create_item(subcategory=subcategory_3)

        response = self._delete(category_3.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        category_3.refresh_from_db()
        self.assertIsNotNone(category_3.deleted_at)

        subcategory_3.refresh_from_db()
        self.assertIsNotNone(subcategory_3.deleted_at)

        item_3.refresh_from_db()
        self.assertIsNotNone(item_3.deleted_at)

    def test_with_subcategory(self):
        category_1 = Manager.create_category()

        subcategory_1 = Manager.create_subcategory(parent=category_1)

        response = self._delete(subcategory_1.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        category_1.refresh_from_db()
        self.assertIsNone(category_1.deleted_at)

        subcategory_1.refresh_from_db()
        self.assertIsNotNone(subcategory_1.deleted_at)

        subcategory_2 = Manager.create_subcategory(parent=category_1)
        item_2 = Manager.create_item(subcategory=subcategory_2)

        subcategory_3 = Manager.create_subcategory(parent=category_1)
        item_3 = Manager.create_item(subcategory=subcategory_3)

        category_1.refresh_from_db()
        self.assertEqual(category_1.item_count, 2)

        response = self._delete(subcategory_2.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        category_1.refresh_from_db()
        self.assertIsNone(category_1.deleted_at)
        self.assertEqual(category_1.item_count, 1)

        subcategory_2.refresh_from_db()
        self.assertIsNotNone(subcategory_2.deleted_at)

        item_2.refresh_from_db()
        self.assertIsNotNone(item_2.deleted_at)

        subcategory_3.refresh_from_db()
        self.assertIsNone(subcategory_3.deleted_at)

        item_3.refresh_from_db()
        self.assertIsNone(item_3.deleted_at)

    def test_failure_with_invalid_id(self):
        response = self._delete(9999999, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_category_or_subcategory_with_menu_items(self):
        category = Manager.create_category()

        subcategory_with_menu_items = Manager.create_subcategory(parent=category)
        menu_item = Manager.create_menu_item(data=Data.valid_menu_item_data(subcategory=subcategory_with_menu_items))

        subcategory_without_menu_items = Manager.create_subcategory(parent=category)
        Manager.create_item(subcategory=subcategory_without_menu_items)

        response = self._delete(category.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "This category has associated menu items. It can't be deleted")

        response = self._delete(subcategory_with_menu_items.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "This category has associated menu items. It can't be deleted")

        response = self._delete(subcategory_without_menu_items.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        category.refresh_from_db()
        self.assertEqual(category.item_count, 1)

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._delete(999, Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._delete(999, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._delete(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._delete(999))
