from rest_framework.test import APIClient
from rest_framework import status

from ...payment.models import Payment
from ...order.models import Order
from ...driver.models import Driver

from ...tests.TestCase import TestCase

from ..utils import Data, Manager, Point
from ...driver_payment.models import DriverPayment
from ...venue_payment.models import VenuePayment
from ...setting.models import Setting

import time

from ...company.models import Company

from ...all_time_stat.models import AllTimeStat
from ...utils import Constants, DateUtils, Api


class EditTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.order = Manager.create_order()

        self.staff = Manager.create_staff(venue=self.order.venue)

        self.member_access_token = Manager.get_access_token(self.staff.company_member.user)

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/orders/{id}", data, access_token)

        return response

    def test_success_with_changing_status_to_looking_for_drivers(self):
        venue = self.order.venue
        company = venue.company

        company_total_accept_time = company.total_accept_time
        company_average_accept_time = company.average_accept_time

        data = {
            "status": Constants.ORDER_STATUS_LOOKING_FOR_DRIVER
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["status"], data["status"])

        company.refresh_from_db()

        venue.refresh_from_db()

        self.order.refresh_from_db()

        self.assertEqual(venue.total_accept_time, company.total_accept_time)
        self.assertNotEqual(company.total_accept_time, company_total_accept_time)

        self.assertNotEqual(company.total_accept_time, company_total_accept_time)
        self.assertNotEqual(company.average_accept_time, company_average_accept_time)

        self.assertIsNotNone(self.order.started_looking_for_drivers_at)
        self.assertIsNone(self.order.rejected_at)
        self.assertIsNone(self.order.collected_at)
        self.assertIsNone(self.order.returned_at)
        self.assertIsNone(self.order.payment.refunded_at)

    def test_success_with_changing_status_to_rejected(self):
        venue = self.order.venue
        company = venue.company

        company_total_accept_time = company.total_accept_time
        company_average_accept_time = company.average_accept_time

        all_time_stats_rejected = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_REJECTED_ORDER_COUNT)

        data = {
            "status": Constants.ORDER_STATUS_REJECTED
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["status"], data["status"])

        payment = Payment.objects.get(id=self.order.payment.id)

        self.assertIsNotNone(payment.refunded_at)
        self.assertIsNotNone(payment.stripe_refund_id)

        company.refresh_from_db()

        venue.refresh_from_db()

        self.order.refresh_from_db()

        self.assertEqual(venue.total_accept_time, company.total_accept_time)
        self.assertEqual(company.total_accept_time, company_total_accept_time)
        self.assertEqual(company.average_accept_time, company_average_accept_time)

        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_REJECTED_ORDER_COUNT), all_time_stats_rejected+1)

        self.assertIsNotNone(self.order.rejected_at)
        self.assertIsNone(self.order.started_looking_for_drivers_at)
        self.assertIsNone(self.order.collected_at)
        self.assertIsNone(self.order.returned_at)
        self.assertEqual(self.order.rejection_reason, Constants.ORDER_REJECTION_REASON_REJECTED_BY_VENUE)

    def test_success_with_changing_delivery_status_to_out_for_delivery(self):
        venue = self.order.venue
        delivery_request = Manager.assign_a_driver_to_order(venue=venue)
        order = delivery_request.order

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json["delivery_status"], data["delivery_status"])
        self.assertEqual(response.json["status"], Constants.ORDER_STATUS_ACCEPTED)

        order.refresh_from_db()

        self.assertIsNotNone(order.collected_at)

    def test_success_with_changing_delivery_status_to_delivered_with_identification_not_requested(self):
        venue = self.order.venue
        delivery_request = Manager.assign_a_driver_to_order(venue=venue)

        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        self.assertIsNotNone(driver.current_delivery_request)

        order = delivery_request.order

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        driver_before = driver
        venue_before = order.venue
        company_before = order.venue.company

        all_time_stat_total_wait_before = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_TOTAL_WAIT_TIME)
        all_time_stat_average_wait_before = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_AVERAGE_WAIT_TIME)
        all_time_stat_delivered_order_count_before = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DELIVERED_ORDER_COUNT)

        Order.objects.filter(id=order.id).update(collected_at= DateUtils.minutes_before(3))

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED,
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUESTED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()

        self.assertIsNotNone(order.delivered_at)
        self.assertEqual(order.driver, driver)
        self.assertEqual(order.delivery_status, data["delivery_status"])
        self.assertIsNone(order.identification)
        self.assertEqual(order.identification_status, data["identification_status"])

        self.assertIsNone(Driver.objects.get(user_id=driver.user_id).current_delivery_request)

        self.check_delivered_order_stats(order, driver_before, venue_before, company_before, all_time_stat_total_wait_before, all_time_stat_average_wait_before, all_time_stat_delivered_order_count_before)

    def test_success_with_changing_delivery_status_to_delivered_with_identification_not_required(self):
        venue = self.order.venue
        delivery_request = Manager.assign_a_driver_to_order(venue=venue)
        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        order = delivery_request.order

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        driver_before = driver
        venue_before = order.venue
        company_before = order.venue.company

        all_time_stat_total_wait_before = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_TOTAL_WAIT_TIME)
        all_time_stat_average_wait_before = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_AVERAGE_WAIT_TIME)
        all_time_stat_delivered_order_count_before = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DELIVERED_ORDER_COUNT)

        Order.objects.filter(id=order.id).update(collected_at=DateUtils.minutes_before(3))

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED,
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUIRED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()

        self.assertIsNotNone(order.delivered_at)
        self.assertEqual(order.driver, driver)
        self.assertEqual(order.delivery_status, data["delivery_status"])
        self.assertIsNone(order.identification)
        self.assertEqual(order.identification_status, data["identification_status"])

        self.check_delivered_order_stats(order, driver_before, venue_before, company_before,
                                         all_time_stat_total_wait_before, all_time_stat_average_wait_before,
                                         all_time_stat_delivered_order_count_before)

    def test_success_with_changing_delivery_status_to_failed_with_no_answer(self):
        venue = self.order.venue
        delivery_request = Manager.assign_a_driver_to_order(venue=venue)
        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        order = delivery_request.order

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        Order.objects.filter(id=order.id).update(collected_at=DateUtils.minutes_before(3))
        point = Point.from_db_to_lat_and_lng(driver.last_known_location)

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_FAILED,
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_PROVIDED,
            "driver_location_latitude": point["latitude"],
            "driver_location_longitude": point["longitude"],
            "no_answer_image": Manager.create_image().id
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()

        self.assertIsNone(order.delivered_at)
        self.assertIsNotNone(order.failed_at)
        self.assertEqual(order.driver, driver)
        self.assertEqual(order.delivery_status, data["delivery_status"])
        self.assertIsNone(order.identification)
        self.assertEqual(order.identification_status, data["identification_status"])
        self.assertIsNotNone(order.no_answer_driver_location)
        self.assertEqual(order.no_answer_image.id, data["no_answer_image"])

    def test_success_with_changing_delivery_status_to_delivered_with_identification_provided(self):
        venue = self.order.venue
        delivery_request = Manager.assign_a_driver_to_order(venue=venue)
        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        order = delivery_request.order

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        driver_before = driver
        venue_before = order.venue
        company_before = order.venue.company

        all_time_stat_total_wait_before = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_TOTAL_WAIT_TIME)
        all_time_stat_average_wait_before = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_AVERAGE_WAIT_TIME)
        all_time_stat_delivered_order_count_before = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DELIVERED_ORDER_COUNT)

        Order.objects.filter(id=order.id).update(collected_at=DateUtils.minutes_before(3))

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED,
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_PROVIDED,
            "identification": Data.valid_identification_data()
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()

        self.assertIsNotNone(order.delivered_at)
        self.assertEqual(order.driver, driver)
        self.assertEqual(order.delivery_status, data["delivery_status"])
        self.assertIsNotNone(order.identification)
        self.assertEqual(order.identification_status, data["identification_status"])

        self.check_delivered_order_stats(order, driver_before, venue_before, company_before,
                                         all_time_stat_total_wait_before, all_time_stat_average_wait_before,
                                         all_time_stat_delivered_order_count_before)

    def test_success_with_changing_delivery_status_to_failed_with_identification_refused(self):
        venue = self.order.venue
        delivery_request = Manager.assign_a_driver_to_order(venue=venue)
        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        order = delivery_request.order

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        Order.objects.filter(id=order.id).update(collected_at=DateUtils.minutes_before(3))

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_FAILED,
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_REFUSED,
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()

        self.assertIsNone(order.delivered_at)
        self.assertIsNotNone(order.failed_at)
        self.assertEqual(order.driver, driver)
        self.assertEqual(order.delivery_status, data["delivery_status"])
        self.assertIsNone(order.identification)
        self.assertEqual(order.identification_status, data["identification_status"])

        driver_payment = DriverPayment.objects.filter(driver=driver, order=order).first()

        self.assertIsNotNone(driver_payment)
        self.assertEqual(driver_payment.type, Constants.DRIVER_PAYMENT_TYPE_DELIVERY)
        self.assertEqual(driver_payment.amount, order.payment.delivery_driver_fee + order.payment.tip)

    def test_success_with_changing_delivery_status_to_returned(self):
        venue = self.order.venue
        customer = Manager.create_customer()

        driver = Manager.get_driver_close_to_venue(venue=venue)

        order_data = Data.valid_order_data(customer=customer, venue=venue, tip=500)
        order = Manager.create_order(customer=customer, data=order_data, venue=venue)
        order = Manager.create_looking_for_driver_order(order, venue)

        delivery_request = order.delivery_requests.first()

        Manager.assign_a_driver_to_order(driver, delivery_request=delivery_request)

        driver.refresh_from_db()

        driver_access_token = Manager.get_access_token(driver.user)

        self.assertIsNotNone(driver.current_delivery_request)

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        Order.objects.filter(id=order.id).update(collected_at=DateUtils.minutes_before(3))

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_FAILED,
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_REFUSED,
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        driver.refresh_from_db()
        self.assertIsNotNone(driver.current_delivery_request)

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_RETURNED
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        driver.refresh_from_db()
        self.assertIsNone(driver.current_delivery_request)

        order.refresh_from_db()

        self.assertIsNotNone(order.returned_at)
        self.assertEqual(order.delivery_status, data["delivery_status"])

        driver_payment_for_delivery = DriverPayment.objects.filter(driver=driver, order=order, type=Constants.DRIVER_PAYMENT_TYPE_DELIVERY).first()

        self.assertIsNotNone(driver_payment_for_delivery)
        self.assertEqual(driver_payment_for_delivery.type, Constants.DRIVER_PAYMENT_TYPE_DELIVERY)
        self.assertEqual(driver_payment_for_delivery.amount, order.payment.delivery_driver_fee + order.payment.tip)

        driver_payment_for_return = DriverPayment.objects.filter(driver=driver, order=order, type=Constants.DRIVER_PAYMENT_TYPE_RETURN).first()

        self.assertIsNotNone(driver_payment_for_return)
        self.assertEqual(driver_payment_for_return.type, Constants.DRIVER_PAYMENT_TYPE_RETURN)
        self.assertEqual(driver_payment_for_return.amount, order.payment.delivery_driver_fee)

        venue_payment_for_return = VenuePayment.objects.filter(order=order).first()

        self.assertIsNotNone(venue_payment_for_return)
        self.assertEqual(venue_payment_for_return.venue, order.venue)
        self.assertEqual(venue_payment_for_return.amount, order.payment.amount - order.payment.stripe_fee)

    def test_failure_with_company_member_changing_status(self):
        self.order.driver = Manager.create_driver()

        self.order.save()

        data = {
            "status": Constants.ORDER_STATUS_REJECTED
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'You cannot reject this order')

        self.order.status = Constants.ORDER_STATUS_LOOKING_FOR_DRIVER
        self.order.driver = None
        self.order.save()

        data = {
            "status": Constants.ORDER_STATUS_REJECTED
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'You can only change status of pending orders')

        data = {
            "status": Constants.ORDER_STATUS_LOOKING_FOR_DRIVER
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'You can only change status of pending orders')

        data = {
            "status": Constants.ORDER_STATUS_ACCEPTED
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["status"]["status"], "'status needs to be one of ['looking_for_driver', 'rejected']'")

        self.order.status = Constants.ORDER_STATUS_PENDING
        self.order.save()

        data = {
            "status": Constants.ORDER_STATUS_LOOKING_FOR_DRIVER,
            "delivery_status": Constants.DELIVERY_STATUS_RETURNED
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'You cannot edit status and delivery status at the same time')

        self.order.driver = Manager.create_driver()
        self.order.save()

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_RETURNED
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Order status has to be failed')

    def test_failure_with_changing_delivery_status_out_for_delivery_or_returned(self):
        data = {
            "delivery_status": "random"
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_status"][0], '"random" is not a valid choice.')

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Order has to have a driver assigned to change delivery status')

        self.order.delivery_status = Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        self.order.driver = Manager.create_driver()
        self.order.save()

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(self.order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Order status has to be pending')

    def test_failure_with_driver_changing_delivery_status(self):
        venue = self.order.venue
        delivery_request = Manager.assign_a_driver_to_order(venue=venue)
        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        order = delivery_request.order

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self._patch(order.id, {}, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'identification_status is required')

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_REFUSED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'delivery_status is required')

        data = {
            "identification_status": "random",
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_status"]["delivery_status"], "'delivery_status needs to be one of ['failed', 'delivered']'")
        self.assertEqual(response.json["identification_status"]["identification_status"], "'identification_status needs to be one of ['not_requested', 'not_required', 'refused', 'not_provided', 'provided']'")

        order.status = Constants.ORDER_STATUS_PENDING
        order.save()

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_REFUSED,
            "delivery_status": Constants.DELIVERY_STATUS_FAILED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Order needs to be accepted first!')

        order.status = Constants.ORDER_STATUS_ACCEPTED
        order.delivery_status = Constants.DELIVERY_STATUS_PENDING
        order.save()

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_REFUSED,
            "delivery_status": Constants.DELIVERY_STATUS_FAILED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Order status has to be out for delivery')

        order.delivery_status = Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        order.save()

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_REFUSED,
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], "You cannot set delivery status as 'delivered' when customer refused to provide an ID")

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_PROVIDED,
            "delivery_status": Constants.DELIVERY_STATUS_FAILED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], "Identification status is set to 'provided' without providing an identification")

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_PROVIDED,
            "identification": Data.valid_identification_data(),
            "delivery_status": Constants.DELIVERY_STATUS_FAILED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], "You cannot set delivery status as 'failed' when ID is provided")

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUIRED,
            "delivery_status": Constants.DELIVERY_STATUS_FAILED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], "You cannot set delivery status as 'failed' when ID is not required")

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUESTED,
            "delivery_status": Constants.DELIVERY_STATUS_FAILED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], "You cannot set delivery status as 'failed' when ID is not requested")

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_PROVIDED,
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0],
                         "You cannot set delivery status as 'delivered' when customer does not provide an ID")

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_PROVIDED,
            "delivery_status": Constants.DELIVERY_STATUS_FAILED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0],
                         "no_answer_image and driver_location are required when 'no answer' is selected")

        customer_address = order.data["customer_address"]

        point = Point.north(customer_address["latitude"], customer_address["longitude"], Api.NO_ANSWER_DISTANCE_TO_CUSTOMER_IN_KMS+1)

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_PROVIDED,
            "delivery_status": Constants.DELIVERY_STATUS_FAILED,
            "no_answer_image": Manager.create_image().id,
            "driver_location_latitude": point.latitude,
            "driver_location_longitude": point.longitude,
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0],
                         "You are not close enough to customer to set order as 'no answer'")

        data = {
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUIRED,
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED,
            "no_answer_image": Manager.create_image().id,
            "driver_location_latitude": point.latitude,
            "driver_location_longitude": point.longitude,
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()

        self.assertIsNone(order.no_answer_image)
        self.assertIsNone(order.no_answer_driver_location)

    def test_failure_with_no_identification_while_identification_is_required(self):
        venue = self.order.venue
        delivery_request = Manager.assign_a_driver_to_order(venue=venue)

        driver = delivery_request.driver
        driver_access_token = Manager.get_access_token(driver.user)

        self.assertIsNotNone(driver.current_delivery_request)

        order = delivery_request.order

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        customer = order.customer
        customer.user.date_of_birth = DateUtils.years_before(Setting.get_minimum_age() - 5)
        customer.user.save()

        self.assertIsNotNone(Driver.objects.get(user_id=order.driver.user_id).current_delivery_request)

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED,
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUESTED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.delivery_status = Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        order.save()

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED,
            "identification": Data.valid_identification_data(),
            "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_PROVIDED
        }

        response = self._patch(order.id, data, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(Driver.objects.get(user_id=order.driver.user_id).current_delivery_request)

    def test_failure_with_driver_does_not_belong_to_current_order(self):
        venue = self.order.venue
        delivery_request = Manager.assign_a_driver_to_order(venue=venue)

        order = delivery_request.order

        data = {
            "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
        }

        response = self._patch(order.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self._patch(order.id, {}, Manager.get_driver_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_staff_belongs_to_different_venue_of_same_company(self):
        staff = Manager.create_staff(venue=Manager.create_venue(company=self.order.venue.company))

        access_token = Manager.get_access_token(staff.company_member.user)

        response = self._patch(self.order.id, {}, access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_company_member_belongs_to_different_company(self):
        response = self._patch(self.order.id, {}, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_invalid_id(self):
        response = self._patch(9999, {}, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_admin(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_admin_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))

    def check_delivered_order_stats(self, order, driver_before, venue_before, company_before, all_time_stat_total_wait_before, all_time_stat_average_wait_before, all_time_stat_delivered_order_count_before):
        driver = order.driver
        venue = order.venue
        company = venue.company

        driver_payment = DriverPayment.objects.filter(driver=driver, order=order).first()

        self.assertIsNotNone(driver_payment)
        self.assertEqual(driver_payment.type, Constants.DRIVER_PAYMENT_TYPE_DELIVERY)
        self.assertEqual(driver_payment.amount, order.payment.delivery_driver_fee + order.payment.tip)

        self.assertEqual(driver.total_earnings, driver_before.total_earnings + driver_payment.amount)
        self.assertEqual(driver.delivered_order_count, driver_before.delivered_order_count + 1)
        self.assertNotEqual(driver.total_delivery_time, driver_before.total_delivery_time)
        self.assertNotEqual(driver.average_delivery_time, driver_before.average_delivery_time)
        self.assertEqual(driver.average_delivery_time, round(driver.total_delivery_time/driver.delivered_order_count))

        self.assertEqual(venue.delivered_order_count, venue_before.delivered_order_count + 1)
        self.assertNotEqual(venue.total_delivery_time, venue_before.total_delivery_time)
        self.assertNotEqual(venue.total_delivery_time, venue_before.total_delivery_time)
        self.assertEqual(venue.average_delivery_time, round(venue.total_delivery_time/venue.delivered_order_count))

        self.assertEqual(company.delivered_order_count, company_before.delivered_order_count + 1)
        self.assertNotEqual(company.total_delivery_time, company_before.total_delivery_time)
        self.assertNotEqual(company.total_delivery_time, company_before.total_delivery_time)
        self.assertEqual(company.average_delivery_time, round(company.total_delivery_time/company.delivered_order_count))

        all_time_stat_total_wait = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_TOTAL_WAIT_TIME)
        all_time_stat_average_wait = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_AVERAGE_WAIT_TIME)
        all_time_stat_delivered_order_count = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DELIVERED_ORDER_COUNT)

        self.assertEqual(all_time_stat_delivered_order_count, all_time_stat_delivered_order_count_before + 1)
        self.assertNotEqual(all_time_stat_total_wait, all_time_stat_total_wait_before)
        self.assertNotEqual(all_time_stat_average_wait, all_time_stat_average_wait_before)
        self.assertEqual(all_time_stat_average_wait, round(all_time_stat_total_wait/all_time_stat_delivered_order_count))



