from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ...delivery_request.models import DeliveryRequest

from ..utils import Data, Manager

from ...company.models import Company

from ...utils import Constants


class EditTest(TestCase):

    client = APIClient()

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/delivery-requests/{id}", data, access_token)

        return response

    def test_success_with_reject(self):
        delivery_request = Manager.get_delivery_request()
        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        data = {
            "status": Constants.DELIVERY_REQUEST_STATUS_REJECTED
        }

        response = self._patch(delivery_request.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["rejected_at"])
        self.assertIsNone(response.json["accepted_at"])
        self.assertEqual(response.json["status"], data["status"])

    def test_success_with_accept(self):
        venue = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))
        driver_1 = Manager.get_driver_close_to_venue(venue=venue)
        driver_2 = Manager.get_driver_close_to_venue(venue=venue)
        driver_3 = Manager.get_driver_close_to_venue(venue=venue)

        order = Manager.create_looking_for_driver_order(venue=venue)

        driver_1_access_token = Manager.get_access_token(driver_1.user)

        data = {
            "status": Constants.DELIVERY_REQUEST_STATUS_ACCEPTED
        }

        delivery_request_with_driver_1 = DeliveryRequest.objects.filter(driver=driver_1, order=order).first()

        response = self._patch(delivery_request_with_driver_1.id, data, driver_1_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(response.json["rejected_at"])
        self.assertIsNotNone(response.json["accepted_at"])

        order.refresh_from_db()

        self.assertEqual(order.driver, driver_1)
        self.assertEqual(order.status, Constants.ORDER_STATUS_ACCEPTED)
        self.assertIsNotNone(order.accepted_at)

        driver_1.refresh_from_db()

        self.assertEqual(driver_1.current_delivery_request.id, response.json["id"])
        self.assertEqual(driver_1.order_count, 1)
        self.assertIsNotNone(driver_1.total_accept_time)

        delivery_requests = DeliveryRequest.objects.filter(order=order).exclude(driver=driver_1)

        for delivery_request in delivery_requests:
            self.assertTrue(delivery_request.driver == driver_2 or delivery_request.driver == driver_3)
            self.assertEqual(delivery_request.status, Constants.DELIVERY_REQUEST_STATUS_MISSED)

        delivery_request_with_driver_2 = delivery_requests.filter(driver=driver_2).first()
        driver_2_access_token = Manager.get_access_token(driver_2.user)

        response = self._patch(delivery_request_with_driver_2.id, data, driver_2_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json["DeliveryRequest"][0], 'You can only accept or reject pending delivery requests')

        delivery_request_with_driver_2.status = Constants.DELIVERY_REQUEST_STATUS_PENDING
        delivery_request_with_driver_2.save()

        response = self._patch(delivery_request_with_driver_2.id, data, driver_2_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["DeliveryRequest"][0], 'This request already accepted by different driver')

    def test_with_delivery_request_belongs_to_someone_else(self):
        self.delivery_request = Manager.get_delivery_request()

        response = self._patch(self.delivery_request.id, {}, Manager.get_driver_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_edit_already_edited_delivery_request(self):
        delivery_request = Manager.get_delivery_request()
        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        data = {
            "status": Constants.DELIVERY_REQUEST_STATUS_REJECTED
        }

        response = self._patch(delivery_request.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["rejected_at"])
        self.assertIsNone(response.json["accepted_at"])
        self.assertEqual(response.json["status"], data["status"])

        response = self._patch(delivery_request.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["DeliveryRequest"][0], 'You can only accept or reject pending delivery requests')

    def test_failure_with_editing_to_invalid_status(self):
        delivery_request = Manager.get_delivery_request()

        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        data = {
            "status": "random"
        }

        response = self._patch(delivery_request.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["status"][0], '"random" is not a valid choice.')

        data = {
            "status": Constants.DELIVERY_REQUEST_STATUS_MISSED
        }

        response = self._patch(delivery_request.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["status"]["status"], "'status needs to be one of ['accepted', 'rejected']'")

    def test_with_rejected_order(self):
        delivery_request = Manager.get_delivery_request()
        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        delivery_request.order.status = Constants.ORDER_STATUS_REJECTED
        delivery_request.order.save()

        data = {
            "status": Constants.DELIVERY_REQUEST_STATUS_ACCEPTED
        }

        response = self._patch(delivery_request.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["DeliveryRequest"][0], 'This order is not looking for drivers')

        data = {
            "status": Constants.DELIVERY_REQUEST_STATUS_ACCEPTED
        }

        response = self._patch(delivery_request.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["DeliveryRequest"][0], 'This order is not looking for drivers')

        data = {
            "status": Constants.DELIVERY_REQUEST_STATUS_REJECTED
        }

        response = self._patch(delivery_request.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["status"], data["status"])

        delivery_request.order.status = Constants.ORDER_STATUS_PENDING
        delivery_request.order.save()

    def test_failure_with_admin(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))