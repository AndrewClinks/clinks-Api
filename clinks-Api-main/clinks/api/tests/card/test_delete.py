from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...card.models import Card

from ..utils import Data, Manager


class DeleteTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer = Manager.create_customer()
        self.customer_access_token = Manager.get_access_token(self.customer.user)

        self.card = Manager.create_card(self.customer_access_token)
        self.card_non_default = Manager.create_card(self.customer_access_token, Data.valid_card_data(default=False))

    def _delete(self, id, access_token="", **kwargs):
        response = super()._delete(f"/cards/{id}", access_token)

        return response

    def test_success(self):
        self.assertEqual(Card.objects.filter(customer=self.customer).count(), 2)

        response = self._delete(self.card_non_default.id, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Card.objects.filter(customer=self.customer).count(), 1)

    def test_failure_with_default_card(self):
        response = self._delete(self.card.id, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "You cannot delete the default card")

    def test_failure_with_invalid_id(self):
        response = self._delete(9999, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_card_belongs_to_someone_else(self):
        response = self._delete(self.card.id, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_admin(self):
        self.permission_denied_test(self._delete(999, Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._delete(999, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._delete(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._delete(999))

