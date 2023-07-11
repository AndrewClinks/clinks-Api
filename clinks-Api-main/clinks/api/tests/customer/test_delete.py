import uuid

from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...image.models import Image
from ...customer.models import Customer
from ...identification.models import Identification

from ...utils import DateUtils, Constants, File

from ..utils import Data, Manager


class DeleteTest(TestCase):

    client = APIClient()

    def setUp(self):
        customer_data = Data.valid_customer_data(email=Data.TEST_EMAIL)

        self.email = customer_data["user"]["email"]
        self.password = customer_data["user"]["password"]

        self.customer = Manager.create_customer(customer_data)
        self.customer_access_token = Manager.get_access_token(self.customer.user)

    def _delete(self, id, access_token="", **kwargs):
        response = super()._delete(f"/customers/{id}", access_token)

        return response

    def test_success_with_account_without_orders(self):
        data = Data.valid_customer_data(with_phone_number=True)

        email = data["user"]["email"]
        password = data["user"]["password"]

        customer = Manager.create_customer(data)
        customer_access_token = Manager.get_access_token(customer.user)

        Manager.update_customer(customer, True, True, False)

        customer.refresh_from_db()

        self.assertIsNotNone(customer.user.phone_number)
        self.assertIsNotNone(customer.identification)
        self.assertIsNotNone(customer.address)

        identification = customer.identification

        front = identification.front.__dict__
        back = identification.back.__dict__

        response = self._delete(customer.user_id, customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        customer.refresh_from_db()

        user = customer.user

        self.assertEqual(user.first_name, "deleted")
        self.assertEqual(user.last_name, "user")
        self.assertTrue("deleted" in user.email)
        self.assertEqual(user.status, Constants.USER_STATUS_DELETED)
        self.assertIsNotNone(user.deleted_at)
        self.assertIsNone(user.phone_number)
        self.assertIsNone(user.phone_number)
        self.assertFalse(user.active)

        address = customer.address

        self.assertEqual(address.line_1, "redacted_address_line_1")
        self.assertIsNone(address.line_2)
        self.assertIsNone(address.line_3)
        self.assertIsNone(address.postal_code)
        self.assertEqual(address.point.coords[0], 53.3331671)
        self.assertEqual(address.point.coords[1], -6.243948)

        self.assertIsNone(customer.identification)

        self.assertFalse(Image.objects.filter(id=front["id"]).exists())
        self.assertFalse(Image.objects.filter(id=back["id"]).exists())

        self.assertFalse(File.exists(front["thumbnail"]))
        self.assertFalse(File.exists(front["banner"]))
        self.assertFalse(File.exists(front["original"]))

        self.assertFalse(File.exists(back["thumbnail"]))
        self.assertFalse(File.exists(back["banner"]))
        self.assertFalse(File.exists(back["original"]))

        response = super()._get(f"/customers/{customer.user_id}", access_token=customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json["detail"], "You do not have permission to perform this action.")

        response = Manager.login(email, password)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json["detail"], "A user with this email and password combination does not exist.")

        response = Manager.user_info(customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json["detail"], "You do not have permission to perform this action.")

    def test_success_without_phone_number_identification_and_address(self):
        response = self._delete(self.customer.user_id, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.customer.refresh_from_db()

        user = self.customer.user

        self.assertEqual(user.first_name, "deleted")

    def test_success_with_account_with_orders(self):
        order_without_identification = Manager.create_delivered_order()
        order_without_identification.customer = self.customer
        order_without_identification.save()

        self.assertNotEqual(order_without_identification.data["customer_address"], "redacted_address")

        order_with_identification = Manager.create_delivered_order()
        order_with_identification.customer = self.customer

        order_identification = Manager.create_identification(Data.valid_identification_data(use_mock_image=False))

        order_identification_front = order_identification.front.__dict__
        order_identification_back = order_identification.back.__dict__

        order_with_identification.identification = order_identification
        order_with_identification.save()

        response = self._delete(self.customer.user_id, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        order_without_identification.refresh_from_db()

        self.assertEqual(order_without_identification.data["customer_address"], "redacted_address")

        order_with_identification.refresh_from_db()

        self.assertIsNone(order_with_identification.identification)
        self.assertEqual(order_with_identification.data["customer_address"], "redacted_address")

        self.assertFalse(Image.objects.filter(id=order_identification_front["id"]).exists())
        self.assertFalse(Image.objects.filter(id=order_identification_back["id"]).exists())

        self.assertFalse(File.exists(order_identification_front["thumbnail"]))
        self.assertFalse(File.exists(order_identification_front["banner"]))
        self.assertFalse(File.exists(order_identification_front["original"]))

        self.assertFalse(File.exists(order_identification_back["thumbnail"]))
        self.assertFalse(File.exists(order_identification_back["banner"]))
        self.assertFalse(File.exists(order_identification_back["original"]))

    def test_failure_with_active_order(self):
        Manager.create_order(self.customer)

        response = self._delete(self.customer.user_id, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["detail"], "You cannot delete your account while there is an active order/s")

    def test_with_deleting_account_belongs_to_someone_else(self):
        customer = Manager.create_customer()

        response = self._delete(customer.user_id, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertTrue(Customer.objects.filter(user_id=customer.user_id).exists())

    def test_failure_with_admin(self):
        self.permission_denied_test(self._delete(999, Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._delete(999, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._delete(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._delete(999))