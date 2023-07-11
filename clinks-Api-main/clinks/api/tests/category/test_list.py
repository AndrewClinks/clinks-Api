from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.category_1 = Manager.create_category()

        self.category_2 = Manager.create_category()

        self.category_2_subcategory = Manager.create_category(Data.valid_category_data(parent=self.category_2))

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/categories", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        query_params_dict = {
            "has_parent": True
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.category_2_subcategory.id)
        self.assertEqual(results[0]["subcategories"], [])
        self.assertIsNotNone(results[0]["parent"])

        self.category_2.sales_count = 2
        self.category_2.save()

        query_params_dict = {
            "order": "most_popular"
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["id"], self.category_2.id)
        self.assertEqual(results[1]["id"], self.category_1.id)

        query_params_dict = {
            "search_term": self.category_1.title
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.category_1.id)

        query_params_dict = {
            "search_term": self.category_2_subcategory.title
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.category_2_subcategory.id)

        query_params_dict = {
            "parent_id": self.category_2.id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.category_2_subcategory.id)

        query_params_dict = {
            "parent_id": self.category_2_subcategory.id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params_dict = {
            "has_items": True
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params_dict = {
            "has_menu_items": True
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        item = Manager.create_item()

        query_params_dict = {
            "has_items": True
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        for result in results:
            self.assertEqual(result["item_count"], 1)
            self.assertEqual(result["menu_item_count"], 0)

        menu_item = Manager.create_menu_item()

        query_params_dict = {
            "has_menu_items": True
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        for result in results:
            self.assertEqual(result["item_count"], 1)
            self.assertEqual(result["menu_item_count"], 1)

        query_params_dict = {
            "has_items": True,
            "has_menu_items": True
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        for result in results:
            self.assertEqual(result["item_count"], 1)
            self.assertEqual(result["menu_item_count"], 1)

        query_params_dict = {
            "venue_id": 222
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params_dict = {
            "venue_id": menu_item.menu.venue_id,
            "has_parent": False
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], menu_item.item.subcategory.parent_id)

    def test_with_menu_items(self):
        menu = Manager.setup_menu()

        query_params_dict = {
            "extend_menu_items": True,
            "venue_id": menu.venue_id,
            "has_parent": True
        }

        response = self._get(query_params_dict, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]["menu_items"]), 1)

        Manager.create_menu_item(menu=menu)

        query_params_dict = {
            "extend_menu_items": True,
            "venue_id": menu.venue_id,
            "has_parent": True
        }

        response = self._get(query_params_dict, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)
        self.assertEqual(len(results[0]["menu_items"]), 1)
        self.assertEqual(len(results[1]["menu_items"]), 1)

        Manager.create_menu_item(menu=menu, menu_category=menu.categories.first(), item=menu.items.first().item)

        query_params_dict = {
            "extend_menu_items": True,
            "venue_id": menu.venue_id,
            "has_parent": True
        }

        response = self._get(query_params_dict, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

    def test_failure_with_company_member(self):
        response = self._get(access_token=Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_customer(self):
        response = self._get(access_token=Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_driver(self):
        response = self._get(access_token=Manager.get_driver_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_unauthorized(self):
        response = self._get()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
