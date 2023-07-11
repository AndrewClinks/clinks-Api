from rest_framework.test import APIClient
from rest_framework import status

from ...opening_hour.models import OpeningHour
from ...tests.TestCase import TestCase

from ..utils import Data, Manager, Point as PointHelper
from django.contrib.gis.geos import Point

from ...company.models import Company

from ...utils import Constants, DateUtils


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.menu_item_1 = Manager.create_menu_item()

        data = Data.valid_menu_item_data(self.menu_item_1.menu, self.menu_item_1.menu_category, Manager.create_item(subcategory=Manager.create_subcategory(parent=self.menu_item_1.menu_category.category)))

        self.menu_item_2 = Manager.create_menu_item(data=data)

        data = Data.valid_menu_item_data(price=600, subcategory=self.menu_item_2.item.subcategory)

        self.menu_item_3 = Manager.create_menu_item(data=data)

        self.menu_item_4 = Manager.create_menu_item(data=Data.valid_menu_item_data(price_sale=200))

        self.max_delivery_distance = 5

        Manager.create_delivery_distances(Data.valid_delivery_distances_with(0, self.max_delivery_distance, 1000))

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/menu-items", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 4)

        first_result = results[0]

        self.assertTrue("item" in first_result)
        self.assertTrue("image" in first_result["item"])
        self.assertTrue("venue" in first_result)
        self.assertTrue("address" in first_result["venue"])
        self.assertTrue("company" in first_result["venue"])
        self.assertTrue("logo" in first_result["venue"]["company"])
        self.assertTrue("price" in first_result)
        self.assertTrue("price_sale" in first_result)

    def test_filter_with_admin(self):
        self.filter_with(Constants.USER_ROLE_ADMIN)

    def filter_with(self, role=None):

        base_query_params_dict = {}

        access_token = ""
        match role:
            case Constants.USER_ROLE_ADMIN:
                access_token = self.admin_access_token
            case Constants.USER_ROLE_COMPANY_MEMBER:
                access_token = Manager.get_staff_access_token(venue=self.menu_item_1.menu.venue)
                base_query_params_dict = {
                    "passcode": self.menu_item_1.menu.venue.company.passcode
                }
            case Constants.USER_ROLE_CUSTOMER:
                access_token = Manager.get_customer_access_token()

        query_params_dict = {
            "venue_id": self.menu_item_1.menu.venue.id,
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], self.menu_item_1.id)
        self.assertEqual(results[1]["id"], self.menu_item_2.id)

        query_params_dict = {
            "venue_id": self.menu_item_3.menu.venue.id,
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        result_count = 0 if role == Constants.USER_ROLE_COMPANY_MEMBER else 1

        self.assertEqual(len(results), result_count)

        if role != Constants.USER_ROLE_COMPANY_MEMBER:
            self.assertEqual(results[0]["id"], self.menu_item_3.id)

        query_params_dict = {
            "item_id": self.menu_item_2.item.id,
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.menu_item_2.id)

        query_params_dict = {
            "category_id": self.menu_item_1.menu_category.category.id,
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        result_count = 2 if role == Constants.USER_ROLE_COMPANY_MEMBER else 3

        self.assertEqual(len(results), result_count)

        if role == Constants.USER_ROLE_COMPANY_MEMBER:
            self.assertEqual(results[0]["id"], self.menu_item_1.id)
            self.assertEqual(results[1]["id"], self.menu_item_2.id)
        else:
            self.assertEqual(results[0]["id"], self.menu_item_1.id)
            self.assertEqual(results[1]["id"], self.menu_item_3.id)
            self.assertEqual(results[2]["id"], self.menu_item_2.id)

        query_params_dict = {
            "subcategory_id": self.menu_item_2.item.subcategory.id,
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        result_count = 1 if role == Constants.USER_ROLE_COMPANY_MEMBER else 2

        self.assertEqual(len(results), result_count)

        if role == Constants.USER_ROLE_COMPANY_MEMBER:
            self.assertEqual(results[0]["id"], self.menu_item_2.id)
        else:
            self.assertEqual(results[0]["id"], self.menu_item_3.id)
            self.assertEqual(results[1]["id"], self.menu_item_2.id)

        query_params_dict = {
            "menu_id": self.menu_item_1.menu_id,
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["id"], self.menu_item_1.id)
        self.assertEqual(results[1]["id"], self.menu_item_2.id)

        query_params_dict = {
            "search_term": self.menu_item_1.menu_category.category.title,
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        result_count = 2 if role == Constants.USER_ROLE_COMPANY_MEMBER else 3

        self.assertEqual(len(results), result_count)

        query_params_dict = {
            "search_term": self.menu_item_2.item.subcategory.title,
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        result_count = 1 if role == Constants.USER_ROLE_COMPANY_MEMBER else 2

        self.assertEqual(len(results), result_count)

        query_params_dict = {
            "search_term": self.menu_item_2.item.title.upper(),
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params_dict = {
            "order": "lowest_price",
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        if role == Constants.USER_ROLE_COMPANY_MEMBER:
            self.assertEqual(results[0]["id"], self.menu_item_1.id)
            self.assertEqual(results[1]["id"], self.menu_item_2.id)
        else:
            self.assertEqual(results[0]["id"], self.menu_item_4.id)
            self.assertEqual(results[1]["id"], self.menu_item_3.id)
            self.assertEqual(results[2]["id"], self.menu_item_1.id)
            self.assertEqual(results[3]["id"], self.menu_item_2.id)

        latitude = 53.3331671
        longitude = -6.243948

        query_params_dict = {
            "latitude": latitude,
            "longitude": longitude,
            **base_query_params_dict
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        result_count = 2 if role == Constants.USER_ROLE_COMPANY_MEMBER else 4

        self.assertEqual(len(results), result_count)

        if role is None or role == Constants.USER_ROLE_CUSTOMER:
            north = PointHelper.north(latitude, longitude, self.max_delivery_distance)

            query_params_dict = {
                "latitude": north.latitude,
                "longitude": north.longitude
            }

            response = self._get(query_params_dict, access_token)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            results = response.json["results"]

            self.assertEqual(len(results), 4)

            north = PointHelper.north(latitude, longitude, self.max_delivery_distance+1)

            query_params_dict = {
                "latitude": north.latitude,
                "longitude": north.longitude
            }

            response = self._get(query_params_dict, access_token)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            results = response.json["results"]

            self.assertEqual(len(results), 0)

            north = PointHelper.north(latitude, longitude, self.max_delivery_distance+1)

            self.menu_item_1.menu.venue.address.point = Point(north.longitude, north.latitude)
            self.menu_item_1.menu.venue.address.save()

            north = PointHelper.north(latitude, longitude, 1)

            self.menu_item_3.menu.venue.address.point = Point(north.longitude, north.latitude)
            self.menu_item_3.menu.venue.address.save()

            query_params_dict = {
                "latitude": latitude,
                "longitude": longitude,
                "order": "closest"
            }

            response = self._get(query_params_dict, access_token)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            results = response.json["results"]

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["id"], self.menu_item_4.id)
            self.assertEqual(results[1]["id"], self.menu_item_3.id)
            self.assertEqual(int(results[0]["venue"]["distance"]), 0)
            self.assertEqual(int(results[1]["venue"]["distance"]), 1000)

        OpeningHour.objects.filter(venue_id=self.menu_item_1.menu.venue.id).update(day=DateUtils.weekday(), starts_at=DateUtils.time())

        query_params_dict = {
            "open_now": True,
            **base_query_params_dict
        }
        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        result_count = 4 if role == Constants.USER_ROLE_ADMIN else 2

        self.assertEqual(len(results), result_count)

    def test_with_company_member(self):
        access_token = Manager.get_staff_access_token(venue=self.menu_item_1.menu.venue)

        query_params_dict = {
            "passcode": self.menu_item_1.menu.venue.company.passcode
        }
        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["id"], self.menu_item_1.id)
        self.assertEqual(results[1]["id"], self.menu_item_2.id)

    def test_filter_with_company_member(self):
        self.filter_with(Constants.USER_ROLE_COMPANY_MEMBER)

    def test_with_stripe_not_setup_account(self):
        venue = Manager.create_venue(setup_stripe_account=False)
        Manager.create_menu_item(menu=venue.menu)

        access_token = Manager.get_customer_access_token()

        response = self._get(access_token=access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 4)

    def test_with_staff_without_menu_items(self):
        access_token = Manager.get_staff_access_token()
        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

    def test_failure_with_company_member_without_passcode(self):
        access_token = Manager.get_staff_access_token(venue=self.menu_item_1.menu.venue)

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'passcode is required.')

    def test_failure_with_company_member_incorrect_passcode(self):
        access_token = Manager.get_staff_access_token(venue=self.menu_item_1.menu.venue)

        query_params_dict = {
            "passcode": 999999
        }
        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'Incorrect passcode')

    def test_with_customer(self):
        self.filter_with(Constants.USER_ROLE_CUSTOMER)

    def test_with_unauthorized(self):
        self.filter_with()

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))


