from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...category.models import Category

from ..utils import Manager, Data


class DeleteTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.item = Manager.create_item()

    def _delete(self, id, access_token="", **kwargs):
        response = super()._delete(f"/items/{id}", access_token)

        return response

    def test_success(self):
        subcategory = Category.objects.get(id=self.item.subcategory_id)
        subcategory_item_count = subcategory.item_count
        category_item_count = subcategory.parent.item_count

        response = self._delete(self.item.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        subcategory.refresh_from_db()

        self.assertEqual(subcategory.item_count, subcategory_item_count-1)
        self.assertEqual(subcategory.parent.item_count, category_item_count-1)

    def test_failure_with_invalid_id(self):
        response = self._delete(999, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_one_has_associated_menu_items(self):
        Manager.create_menu_item(Data.valid_menu_item_data(item=self.item, subcategory=self.item.subcategory))

        response = self._delete(self.item.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "This item has associated menu items. It can't be deleted")

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._delete(999, Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._delete(999, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._delete(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._delete(999))
