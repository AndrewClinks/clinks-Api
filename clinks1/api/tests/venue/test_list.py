from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data, Point

from ...utils import DateUtils


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()
        self.venue = Manager.create_venue(data=Data.valid_venue_data(closed_everyday=True))

        self.member = self.venue.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

        self.venue_2 = Manager.create_venue(data=Data.valid_venue_data(title="xyz", address=Data.valid_address_data("line1"), closed_everyday=True))

        self.max_delivery_distance = 5

        Manager.create_delivery_distances(Data.valid_delivery_distances_with(0, self.max_delivery_distance, 1000))

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/venues", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        query_params_dict = {
            "search_term": self.venue.title
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.venue.id)

        query_params_dict = {
            "search_term": self.venue_2.address.line_1
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.venue_2.id)

        query_params_dict = {
            "company_id": self.venue.company.id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        venue_3 = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))
        venue_3.paused = True
        venue_3.save()

        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        query_params_dict = {
            "paused": True
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], venue_3.id)

        query_params_dict = {
            "paused": False
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

    def test_company_member(self):
        response = self._get(access_token=self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.venue.id)

        query_params_dict = {
            "search_term": self.venue_2.address.line_1
        }

        response = self._get(query_params_dict, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        venue_3 = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True, company=self.venue.company))
        venue_3.paused = True
        venue_3.save()

        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        query_params_dict = {
            "paused": True
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], venue_3.id)

        query_params_dict = {
            "paused": False
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

    def test_with_customer(self):
        venue_3 = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))
        venue_3.paused = True
        venue_3.save()

        response = self._get(access_token=Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        self.assertEqual(response.json["total_count"], 2)

    def test_with_unauthorized(self):
        venue_3 = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))
        venue_3.paused = True
        venue_3.save()

        response = self._get(access_token="")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

    def test_filter(self):
        from ...opening_hour.models import OpeningHour
        query_params_dict = {
            "open_now": True
        }

        response = self._get(query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        OpeningHour.objects.create(venue=self.venue, day=DateUtils.weekday(), starts_at=DateUtils.time(), ends_at=DateUtils.minutes_later(60), order=0)

        response = self._get(query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        OpeningHour.objects.filter(venue_id=self.venue.id).update(day=DateUtils.weekday(), starts_at=DateUtils.minutes_later(60))

        response = self._get(query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        latitude = 53.3331671
        longitude = -6.243948

        query_params_dict = {
            "latitude": latitude,
            "longitude": longitude
        }

        response = self._get(query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        north = Point.north(latitude, longitude, self.max_delivery_distance)

        query_params_dict = {
            "latitude": north.latitude,
            "longitude": north.longitude
        }

        response = self._get(query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        north = Point.north(latitude, longitude, self.max_delivery_distance+1)

        query_params_dict = {
            "latitude": north.latitude,
            "longitude": north.longitude
        }

        response = self._get(query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        data = Data.valid_venue_data()
        data["opening_hours"] = []

        venue_without_opening_hours = Manager.create_venue(data=data)

        query_params_dict = {
            "open_now": True
        }

        response = self._get(query_params_dict)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))


