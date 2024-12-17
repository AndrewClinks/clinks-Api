from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.delivery_request = Manager.get_delivery_request()

        self.driver = self.delivery_request.driver

        self.driver_access_token = Manager.get_access_token(self.driver.user)

    def _get(self, id, access_token="", **kwargs):
        response = super()._get(f"/delivery-requests/{id}", access_token=access_token)

        return response

    def test_success(self):
        response = self._get(self.delivery_request.id, self.driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["driver"], self.driver.user_id)

        self.assertEqual(response.json["id"], self.delivery_request.id)

        payment = self.delivery_request.order.payment

        self.assertEqual(response.json["order"]["payment"]["potential_earning"], payment.delivery_driver_fee + payment.tip)

    def test_with_delivery_request_belongs_to_someone_else(self):
        response = self._get(self.delivery_request.id, Manager.get_driver_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"],  'An object with this id does not exist')

    def test_failure_with_invalid_id(self):
        response = self._get(9999, self.driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"],  'An object with this id does not exist')

    def test_failure_with_admin(self):
        self.permission_denied_test(self._get(999, Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(999, Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(999, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get(999))
