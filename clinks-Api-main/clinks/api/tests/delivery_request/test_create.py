from rest_framework.test import APIClient

from ...delivery_request.models import DeliveryRequest
from ...delivery_distance.models import DeliveryDistance
from ...tests.TestCase import TestCase

from ..utils import Data, Manager, Point

from ...utils import Constants, Api


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer = Manager.create_customer()

        self.customer_access_token = Manager.get_access_token(self.customer.user)

        self.venue = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))

        self.menu = self.venue.menu

        self.max_driver_distance_to_venue = Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS

        Manager.create_delivery_distances(Data.valid_delivery_distances_data([Data.valid_delivery_distance_data(ends=self.max_driver_distance_to_venue+3)]))

        self.first_delivery_distance = DeliveryDistance.objects.first()

        self.driver_1 = Manager.create_driver()

    def test_without_any_driver(self):
        Manager.create_looking_for_driver_order()

        delivery_requests = DeliveryRequest.objects.all()

        self.assertEqual(len(delivery_requests), 0)

    def test_without_many_drivers(self):
        venue = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))
        venue_point = venue.address.point

        self.driver_1.last_known_location = venue_point
        self.driver_1.save()

        driver_2 = Manager.create_driver()
        driver_2.last_known_location = Point.north_for_point(venue_point, round(self.first_delivery_distance.ends/2), True)
        driver_2.save()

        driver_3 = Manager.create_driver()
        driver_3.last_known_location = Point.north_for_point(venue_point, round(self.max_driver_distance_to_venue), True)
        driver_3.save()

        driver_4 = Manager.create_driver()
        driver_4.last_known_location = Point.north_for_point(venue_point, round(self.max_driver_distance_to_venue + 1), True)
        driver_4.save()

        driver_5 = Manager.create_driver()
        driver_5.last_known_location = Point.north_for_point(venue_point, round(self.first_delivery_distance.ends), True)
        driver_5.save()

        order = Manager.create_order(venue=venue)

        delivery_requests = DeliveryRequest.objects.all()

        self.assertEqual(len(delivery_requests), 0)

        order = Manager.create_looking_for_driver_order(order=order)

        delivery_requests = DeliveryRequest.objects.all()

        self.assertEqual(len(delivery_requests), 3)

        self.assertEqual(delivery_requests[0].driver, self.driver_1)
        self.assertEqual(delivery_requests[0].driver_location, self.driver_1.last_known_location)

        self.assertEqual(delivery_requests[1].driver, driver_2)
        self.assertEqual(delivery_requests[1].driver_location, driver_2.last_known_location)

        self.assertEqual(delivery_requests[2].driver, driver_3)
        self.assertEqual(delivery_requests[2].driver_location, driver_3.last_known_location)

        for delivery_request in delivery_requests:
            self.assertEqual(delivery_request.status, Constants.DELIVERY_REQUEST_STATUS_PENDING)
            self.assertEqual(delivery_request.order, order)

        order.driver = self.driver_1
        order.save()

        self.driver_1.current_delivery_request = DeliveryRequest.objects.create(driver=self.driver_1, order=order,
                                                                                driver_location=order.venue.address.point)
        self.driver_1.save()

        order_2 = Manager.create_looking_for_driver_order(venue=venue)

        delivery_requests = DeliveryRequest.objects.filter(order=order_2).order_by("driver_id")

        self.assertEqual(len(delivery_requests), 2)

        self.assertEqual(delivery_requests[0].driver, driver_2)
        self.assertEqual(delivery_requests[1].driver, driver_3)

        order_3 = Manager.create_order()
        order_3.driver = driver_2
        order_3.delivery_status = Constants.DELIVERY_STATUS_RETURNED

        order_3 = Manager.create_looking_for_driver_order(venue=venue)

        delivery_requests = DeliveryRequest.objects.filter(order=order_3).order_by("driver_id")

        self.assertEqual(delivery_requests[0].driver, driver_2)
        self.assertEqual(delivery_requests[1].driver, driver_3)

        order.delivery_status = Constants.DELIVERY_STATUS_DELIVERED
        order.save()

        order_4 = Manager.create_looking_for_driver_order(venue=venue)

        delivery_requests = DeliveryRequest.objects.filter(order=order_4).order_by("driver_id")

        self.assertEqual(len(delivery_requests), 2)

        self.assertEqual(delivery_requests[0].driver, driver_2)
        self.assertEqual(delivery_requests[1].driver, driver_3)

    def test_with_driver_with_active_delivery(self):
        venue = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))
        driver_1 = Manager.get_driver_close_to_venue(venue=venue)
        Manager.get_driver_close_to_venue(venue=venue)

        order = Manager.create_looking_for_driver_order(venue=venue)

        delivery_request_with_driver_1 = DeliveryRequest.objects.filter(driver=driver_1, order=order).first()

        delivery_request = Manager.assign_a_driver_to_order(driver=driver_1,
                                                            delivery_request=delivery_request_with_driver_1)

        order.refresh_from_db()

        self.assertIsNotNone(order)
        self.assertEqual(order, delivery_request.order)

        order = Manager.get_order_looking_for_driver_with_close_driver(venue=venue)

        delivery_requests = DeliveryRequest.objects.filter(order=order)

        for delivery_request in delivery_requests:
            self.assertNotEqual(delivery_request.driver, driver_1)


