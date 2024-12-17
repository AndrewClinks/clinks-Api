from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...item.models import Item
from ..utils import Manager, Data


class DeleteTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.menu = Manager.setup_menu()

        self.menu_item_id = self.menu.categories.first().items.first().id

    def _delete(self, id, access_token="", passcode=None, **kwargs):
        endpoint = f"/menu-items/{id}"

        if passcode:
            endpoint += f"?passcode={passcode}"

        response = super()._delete(endpoint, access_token)

        return response

    def test_with_admin(self):
        menu = Manager.setup_menu()

        menu_item = menu.categories.first().items.first()

        menu_item_id = menu_item.id

        item = Item.objects.get(id=menu_item.item.id)

        item_menu_item_count = item.menu_item_count

        subcategory_menu_item_count = item.subcategory.menu_item_count
        subcategory_item_count = item.subcategory.item_count

        category_menu_item_count = item.subcategory.parent.menu_item_count
        category_item_count = item.subcategory.parent.item_count

        response = self._delete(menu_item_id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        item.refresh_from_db()

        self.assertEqual(item.menu_item_count, item_menu_item_count-1)
        self.assertEqual(item.subcategory.menu_item_count, subcategory_menu_item_count - 1)
        self.assertEqual(item.subcategory.item_count, subcategory_item_count)
        self.assertEqual(item.subcategory.parent.menu_item_count, category_menu_item_count - 1)
        self.assertEqual(item.subcategory.parent.item_count, category_item_count)

    def test_success_with_company_member(self):
        access_token = Manager.get_staff_access_token(venue=self.menu.venue)

        response = self._delete(self.menu_item_id, access_token, self.menu.venue.company.passcode)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_failure_with_company_member_without_passcode(self):
        access_token = Manager.get_staff_access_token(self.menu.venue)

        response = self._delete(self.menu_item_id, access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'passcode is required.')

    def test_failure_with_company_member_incorrect_passcode(self):
        access_token = Manager.get_staff_access_token(self.menu.venue)

        response = self._delete(self.menu_item_id, access_token, 99999)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'Incorrect passcode')

    def test_failure_with_member_belongs_to_different_company(self):
        response = self._delete(self.menu_item_id, Manager.get_company_member_access_token(), 99999)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_failure_with_member_belongs_to_same_company_but_not_in_venue_staff(self):
        member_access_token = Manager.get_company_member_access_token(company=self.menu.venue.company)

        response = self._delete(self.menu_item_id, member_access_token, self.menu.venue.company.passcode)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_failure_with_staff_not_in_venue_staff(self):
        access_token = Manager.get_staff_access_token(company=self.menu.venue.company)

        response = self._delete(self.menu_item_id, access_token, self.menu.venue.company.passcode)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_failure_with_invalid_id(self):
        response = self._delete(9999, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_failure_with_customer(self):
        self.permission_denied_test(self._delete(999, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._delete(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._delete(999))
