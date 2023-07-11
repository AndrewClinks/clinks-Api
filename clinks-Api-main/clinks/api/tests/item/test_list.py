from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.gis.geos import Point
from ...opening_hour.models import OpeningHour

from ...utils import DateUtils, Constants

from ..utils import Manager, Data, Point as PointHelper


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.item_1 = Manager.create_item()
        self.item_1.sales_count = 10
        self.item_1.save()

        self.item_2 = Manager.create_item(subcategory=self.item_1.subcategory)

        self.item_3 = Manager.create_item(subcategory=Manager.create_subcategory(parent=self.item_1.subcategory.parent))

        self.item_4 = Manager.create_item()

        self.max_delivery_distance = 5

        Manager.create_delivery_distances(Data.valid_delivery_distances_with(0, self.max_delivery_distance, 1000))

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/items", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 4)

        query_params_dict = {
            "category_id": self.item_1.subcategory.parent_id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["id"], self.item_1.id)
        self.assertEqual(results[1]["id"], self.item_2.id)
        self.assertEqual(results[2]["id"], self.item_3.id)

        query_params_dict = {
            "subcategory_id": self.item_1.subcategory.parent_id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params_dict = {
            "subcategory_id": self.item_1.subcategory_id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["id"], self.item_1.id)
        self.assertEqual(results[1]["id"], self.item_2.id)

        query_params_dict = {
            "subcategory_id": self.item_3.subcategory_id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.item_3.id)

        query_params_dict = {
            "search_term": self.item_1.subcategory.parent.title
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["id"], self.item_1.id)
        self.assertEqual(results[1]["id"], self.item_2.id)
        self.assertEqual(results[2]["id"], self.item_3.id)

        query_params_dict = {
            "subcategory_id": self.item_1.subcategory.parent_id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        # self.item_1.subcategory.title = "lager"
        # self.item_1.subcategory.save()

        query_params_dict = {
            "search_term": self.item_1.subcategory.title[10:]
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["id"], self.item_1.id)
        self.assertEqual(results[1]["id"], self.item_2.id)

        query_params_dict = {
            "search_term": self.item_4.title[6:]
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.item_4.id)

        query_params_dict = {
            "order": "most_popular"
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(results[0]["id"], self.item_1.id)

    def test_with_company_member(self):
        response = self._get(access_token=Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_with_customer(self):
        response = self._get(access_token=Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_with_customer(self):
        access_token = Manager.get_customer_access_token()

        latitude = 53.3331671
        longitude = -6.243948

        query_params_dict = {
            "latitude": latitude,
            "longitude": longitude
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        menu_item_1 = Manager.create_menu_item(Data.valid_menu_item_data(price=600, item=self.item_1))
        menu_item_2 = Manager.create_menu_item(Data.valid_menu_item_data(price_sale=400, item=self.item_1))
        menu_item_3 = Manager.create_menu_item(item=self.item_2)

        latitude = 53.3331671
        longitude = -6.243948

        query_params_dict = {
            "latitude": latitude,
            "longitude": longitude
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["id"], self.item_1.id)
        self.assertEqual(results[0]["menu_item"]["price"], menu_item_2.price_sale)

        self.assertEqual(results[1]["id"], self.item_2.id)
        self.assertEqual(results[1]["menu_item"]["price"], menu_item_3.price)

        north = PointHelper.north(latitude, longitude, self.max_delivery_distance)

        query_params_dict = {
            "latitude": north.latitude,
            "longitude": north.longitude
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        north = PointHelper.north(latitude, longitude, self.max_delivery_distance + 1)

        query_params_dict = {
            "latitude": north.latitude,
            "longitude": north.longitude
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        north = PointHelper.north(latitude, longitude, self.max_delivery_distance + 1)

        menu_item_2.menu.venue.address.point = Point(north.longitude, north.latitude)
        menu_item_2.menu.venue.address.save()

        north = PointHelper.north(latitude, longitude, 1)

        menu_item_3.menu.venue.address.point = Point(north.longitude, north.latitude)
        menu_item_3.menu.venue.address.save()

        query_params_dict = {
            "latitude": latitude,
            "longitude": longitude,
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["id"], self.item_1.id)
        self.assertEqual(results[0]["menu_item"]["price"], menu_item_1.price)

        self.assertEqual(results[1]["id"], self.item_2.id)
        self.assertEqual(results[1]["menu_item"]["price"], menu_item_3.price)

        query_params_dict = {
            "open_now": True
        }
        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        OpeningHour.objects.filter(venue_id=menu_item_1.menu.venue.id).update(day=DateUtils.weekday(),
                                                                              starts_at=DateUtils.time())

        query_params_dict = {
            "open_now": True
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.item_1.id)
        self.assertEqual(results[0]["menu_item"]["price"], menu_item_1.price)

        query_params_dict = {
            "has_menu_item": True
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        for result in results:
            self.assertNotEqual(result["menu_item_count"], 0)

        company_of_menu_item_1 = menu_item_1.menu.venue.company
        company_of_menu_item_1.status = Constants.COMPANY_STATUS_PAUSED
        company_of_menu_item_1.save()

        company_of_menu_item_2 = menu_item_2.menu.venue.company
        company_of_menu_item_2.status = Constants.COMPANY_STATUS_PAUSED
        company_of_menu_item_2.save()

        query_params_dict = {
            "has_menu_item": True
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.item_2.id)

    def test_with_driver(self):
        response = self._get(access_token=Manager.get_driver_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_with_unauthorized(self):
        response = self._get()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
