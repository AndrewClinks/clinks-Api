import celery.app.task

from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...delivery_request.models import DeliveryRequest
from ...all_time_stat.models import AllTimeStat

from ...tasks import cancel_driver_not_found_or_expired_orders, _create_delivery_requests, create_delivery_requests
from ...utils import Constants, DateUtils, Api
from ..utils import Manager, Data


class TaskTest(TestCase):

    client = APIClient()

    def test_cancel_driver_not_found_or_expired_orders(self):
        expired_order_count = AllTimeStat.get(Constants.ALL_TIME_STAT_EXPIRED_ORDER_COUNT)

        order = Manager.create_order()
        order.created_at = DateUtils.now()
        order.save()

        cancel_driver_not_found_or_expired_orders()

        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_EXPIRED_ORDER_COUNT), expired_order_count)

        order.refresh_from_db()

        self.assertEqual(order.status, Constants.ORDER_STATUS_PENDING)

        order.created_at = DateUtils.minutes_before(35)
        order.save()

        cancel_driver_not_found_or_expired_orders()

        order.refresh_from_db()

        self.assertEqual(order.status, Constants.ORDER_STATUS_REJECTED)
        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_EXPIRED_ORDER_COUNT), expired_order_count+1)
        self.assertEqual(order.rejection_reason, Constants.ORDER_REJECTION_REASON_EXPIRED)
        self.assertIsNotNone(order.payment.refunded_at)
        self.assertIsNotNone(order.payment.stripe_refund_id)

        order = Manager.create_order()

        Manager.create_looking_for_driver_order(order=order)

        cancel_driver_not_found_or_expired_orders()

        order.refresh_from_db()

        self.assertEqual(order.status, Constants.ORDER_STATUS_LOOKING_FOR_DRIVER)

        order.started_looking_for_drivers_at = DateUtils.minutes_before(25)
        order.save()

        cancel_driver_not_found_or_expired_orders()

        order.refresh_from_db()

        self.assertEqual(order.status, Constants.ORDER_STATUS_LOOKING_FOR_DRIVER)

        order = Manager.create_out_for_delivery_order()
        order.started_looking_for_drivers_at = DateUtils.minutes_before(35)
        order.save()

        cancel_driver_not_found_or_expired_orders()

        order.refresh_from_db()

        self.assertEqual(order.status, Constants.ORDER_STATUS_ACCEPTED)

    def test_cancel_driver_not_found_or_expired_orders_when_there_are_drivers_close(self):
        order = Manager.create_order()
        count_of_no_driver_orders = AllTimeStat.get(Constants.ALL_TIME_STAT_NO_DRIVER_FOUND_ORDER_COUNT)
        driver_1 = Manager.get_driver_close_to_venue(venue=order.venue)
        Manager.get_driver_close_to_venue(venue=order.venue)
        Manager.get_driver_close_to_venue(venue=order.venue)

        Manager.create_looking_for_driver_order(order)

        order.refresh_from_db()

        order.started_looking_for_drivers_at = DateUtils.minutes_before(30)
        order.save()

        cancel_driver_not_found_or_expired_orders()

        order.refresh_from_db()

        self.assertEqual(order.status, Constants.ORDER_STATUS_REJECTED)
        self.assertEqual(order.rejection_reason, Constants.ORDER_REJECTION_REASON_NO_DRIVER_FOUND)
        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_NO_DRIVER_FOUND_ORDER_COUNT),  count_of_no_driver_orders + 1)

        self.assertIsNotNone(order.payment.refunded_at)

        delivery_requests = order.delivery_requests.all()

        for delivery_request in delivery_requests:
            self.assertEqual(delivery_request.status, Constants.DELIVERY_REQUEST_STATUS_EXPIRED)

        delivery_request = DeliveryRequest.objects.filter(driver=driver_1).first()

        driver_1_access_token = Manager.get_access_token(driver_1.user)

        response = super()._patch(f"/delivery-requests/{delivery_request.id}", {"status": Constants.DELIVERY_REQUEST_STATUS_ACCEPTED}, driver_1_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["DeliveryRequest"][0], 'You can only accept or reject pending delivery requests')

        staff_access_token = Manager.get_staff_access_token(venue=order.venue)

        data = {
            "status": Constants.ORDER_STATUS_LOOKING_FOR_DRIVER
        }

        response = super()._patch(f"/orders/{order.id}", data, staff_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'You can only change status of pending orders')

        data = {
            "status": Constants.ORDER_STATUS_REJECTED
        }

        response = super()._patch(f"/orders/{order.id}", data, staff_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'You can only change status of pending orders')

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED,
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUIRED
        }

        response = super()._patch(f"/orders/{order.id}", data, driver_1_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

        order = Manager.create_order()

        driver_1 = Manager.get_driver_close_to_venue(venue=order.venue)
        Manager.get_driver_close_to_venue(venue=order.venue)
        Manager.get_driver_close_to_venue(venue=order.venue)

        Manager.create_looking_for_driver_order(order)

        order.refresh_from_db()

        driver_1_access_token = Manager.get_access_token(driver_1.user)

        rejected_delivery_request = DeliveryRequest.objects.filter(driver=driver_1).first()

        response = super()._patch(f"/delivery-requests/{rejected_delivery_request.id}",
                                  {"status": Constants.DELIVERY_REQUEST_STATUS_REJECTED}, driver_1_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        rejected_delivery_request.refresh_from_db()

        order.started_looking_for_drivers_at = DateUtils.minutes_before(30)
        order.save()

        cancel_driver_not_found_or_expired_orders()

        order.refresh_from_db()

        self.assertEqual(order.status, Constants.ORDER_STATUS_REJECTED)
        self.assertEqual(order.rejection_reason, Constants.ORDER_REJECTION_REASON_NO_DRIVER_FOUND)

        self.assertIsNotNone(order.payment.refunded_at)

        delivery_requests = order.delivery_requests.all()

        for delivery_request in delivery_requests:
            if delivery_request.id == rejected_delivery_request.id:
                self.assertEqual(delivery_request.status, Constants.DELIVERY_REQUEST_STATUS_REJECTED)
            else:
                self.assertEqual(delivery_request.status, Constants.DELIVERY_REQUEST_STATUS_EXPIRED)

        delivery_request.refresh_from_db()

    def test_look_for_drivers_when_no_drivers_found_for_an_order(self):
        count_of_delivery_requests = DeliveryRequest.objects.count()

        order = Manager.create_order()

        order_2 = Manager.create_order()
        order_2.status = Constants.ORDER_STATUS_REJECTED
        order_2.save()

        order_3 = Manager.create_order()

        Manager.create_looking_for_driver_order(order)

        order.refresh_from_db()

        delivery_requests = DeliveryRequest.objects.filter(order=order)

        self.assertEqual(delivery_requests.count(), 0)

        driver_1 = Manager.get_driver_close_to_venue(venue=order.venue,
                                                     distance_to_venue=Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS)

        driver_2 = Manager.get_driver_close_to_venue(venue=order.venue)

        Manager.create_driver()

        _create_delivery_requests(order.id, Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS)

        delivery_requests = DeliveryRequest.objects.filter(order=order)

        self.assertEqual(delivery_requests.count(), 2)

        self.assertEqual(delivery_requests.first().driver, driver_1)
        self.assertEqual(delivery_requests.first().order, order)

        self.assertEqual(delivery_requests.last().driver, driver_2)
        self.assertEqual(delivery_requests.last().order, order)

        self.assertEqual(DeliveryRequest.objects.count(), count_of_delivery_requests+2)

        _create_delivery_requests(order.id, Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS)

        delivery_requests = DeliveryRequest.objects.filter(order=order)

        self.assertEqual(delivery_requests.count(), 2)

        Manager.get_driver_close_to_venue(venue=order.venue)

        _create_delivery_requests(order.id, Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS)

        delivery_requests = DeliveryRequest.objects.filter(order=order)

        self.assertEqual(delivery_requests.count(), 3)

        order.driver = driver_1
        order.save()

        driver_1.current_delivery_request = DeliveryRequest.objects.create(driver=driver_1, order=order, driver_location=order.venue.address.point)
        driver_1.save()

        Manager.get_driver_close_to_venue(venue=order_3.venue)
        Manager.get_driver_close_to_venue(venue=order_3.venue, distance_to_venue=Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS+1)

        Manager.create_looking_for_driver_order(order_3)

        delivery_requests = DeliveryRequest.objects.filter(order=order_3)

        self.assertEqual(delivery_requests.count(), 3)

        self.assertFalse(delivery_requests.filter(driver=driver_1).exists())

    def test_check_if_creates_delivery_request_for_rejected_drivers(self):
        order = Manager.create_order()

        driver_1 = Manager.get_driver_close_to_venue(venue=order.venue)
        Manager.get_driver_close_to_venue(venue=order.venue)

        order = Manager.create_looking_for_driver_order()

        delivery_requests = DeliveryRequest.objects.filter(order=order, status=Constants.DELIVERY_REQUEST_STATUS_PENDING)

        self.assertEqual(delivery_requests.count(), 2)

        Manager.reject_a_delivery_request(delivery_requests.filter(driver=driver_1).first())

        _create_delivery_requests(order.id, Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS)

        delivery_requests = DeliveryRequest.objects.filter(order=order,
                                                           status=Constants.DELIVERY_REQUEST_STATUS_PENDING)

        self.assertEqual(delivery_requests.count(), 1)

        order = Manager.create_looking_for_driver_order()

        delivery_requests = DeliveryRequest.objects.filter(order=order, status=Constants.DELIVERY_REQUEST_STATUS_PENDING)

        self.assertEqual(delivery_requests.count(), 2)

        self.assertTrue(delivery_requests.filter(driver=driver_1).exists())

    def test_check_if_creates_more_delivery_requests_after_an_order_accepted(self):
        order = Manager.create_order()

        driver_1 = Manager.get_driver_close_to_venue(venue=order.venue)
        Manager.get_driver_close_to_venue(venue=order.venue)

        order = Manager.create_looking_for_driver_order()

        delivery_requests = DeliveryRequest.objects.filter(order=order, status=Constants.DELIVERY_REQUEST_STATUS_PENDING)

        self.assertEqual(delivery_requests.count(), 2)

        Manager.accept_a_delivery_request(delivery_requests.filter(driver=driver_1).first())

        delivery_requests = DeliveryRequest.objects.filter(order=order, status=Constants.DELIVERY_REQUEST_STATUS_PENDING)

        self.assertEqual(delivery_requests.count(), 0)

        delivery_requests = DeliveryRequest.objects.filter(order=order,
                                                           status=Constants.DELIVERY_REQUEST_STATUS_MISSED)

        self.assertEqual(delivery_requests.count(), 1)

        try:
            _create_delivery_requests(order.id, Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS)
        except Exception as e:
            self.assertTrue("isn't looking for drivers" in e.__dict__["detail"])

    def test_check_if_distance_increases_if_no_drivers_found(self):
        order = Manager.create_order()

        Manager.get_driver_close_to_venue(venue=order.venue,
                                          distance_to_venue=Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS)

        Manager.create_looking_for_driver_order(order)

        delivery_requests = DeliveryRequest.objects.filter(order=order,
                                                           status=Constants.DELIVERY_REQUEST_STATUS_PENDING)

        self.assertEqual(delivery_requests.count(), 1)

        _create_delivery_requests(order.id, Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS)




