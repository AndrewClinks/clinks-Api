from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...delivery_distance.models import DeliveryDistance

from ..utils import Manager, Data, Point


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.venue = Manager.create_venue()

        Manager.create_delivery_distances()

    def _get(self, venue_id, query_params_dict=None, access_token="", **kwargs):
        response = super()._get(f"/delivery-fees/{venue_id}", query_params_dict, access_token=access_token)

        return response

    def test_success(self):
        location = Point.from_db_to_lat_and_lng(self.venue.address.point)

        query_params_dict = {
            "latitude": str(location["latitude"]),
            "longitude": str(location["longitude"])
        }

        response = self._get(self.venue.id, query_params_dict, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json["fee"], DeliveryDistance.objects.first().fee)

        query_params_dict = {
            "latitude": str(location["latitude"]),
            "longitude": str(location["longitude"])
        }

        response = self._get(self.venue.id, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_invalid_id(self):
        location = Point.from_db_to_lat_and_lng(self.venue.address.point)

        query_params_dict = {
            "latitude": str(location["latitude"]),
            "longitude": str(location["longitude"])
        }

        response = self._get(99999999, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "Please check id")

    def test_failure_without_location(self):
        response = self._get(99999999)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"],  "'latitude' and 'longitude' are required")

        location = Point.from_db_to_lat_and_lng(self.venue.address.point)

        query_params_dict = {
            "latitude": str(location["latitude"])
        }

        response = self._get(99999999, query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "'latitude' and 'longitude' are required")

    def test_failure_with_out_of_delivery_distance(self):
        location = Point.north_for_point(self.venue.address.point, int(DeliveryDistance.max_delivery_distance())+1)

        query_params_dict = {
            "latitude": str(location.latitude),
            "longitude": str(location.longitude)
        }

        response = self._get(self.venue.id, query_params_dict, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'Venue cannot deliver to this location')

    def test_failure_with_admin(self):
        self.permission_denied_test(self._get(999, access_token=Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(999, access_token=Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(999, access_token=Manager.get_driver_access_token()))


