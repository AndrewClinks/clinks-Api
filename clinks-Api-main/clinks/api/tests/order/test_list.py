from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...utils import Constants
from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        Manager.create_delivery_distances()

        self.order = Manager.create_order()

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/orders", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertTrue(len(results), 1)

        query_params = {
            "statuses": Constants.ORDER_STATUS_ACCEPTED
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params = {
            "delivery_statuses": Constants.DELIVERY_STATUS_PENDING
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        driver = Manager.create_driver()

        query_params = {
            "driver_id": driver.user_id
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params = {
            "venue_id": self.order.venue_id
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "customer_id": self.order.customer.user_id
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "search_term": self.order.venue.title
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

    def test_with_customer(self):
        customer_access_token = Manager.get_access_token(self.order.customer.user)

        response = self._get(access_token=customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertTrue(len(results), 1)

        self.assertEqual(response.json["total_count"], len(results))

        response = self._get(access_token=Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params = {
            "statuses": Constants.ORDER_STATUS_ACCEPTED
        }

        response = self._get(query_params, customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params = {
            "delivery_statuses": Constants.DELIVERY_STATUS_PENDING
        }

        response = self._get(query_params, customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        driver = Manager.create_driver()

        query_params = {
            "driver_id": driver.user_id
        }

        response = self._get(query_params, customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "venue_id": self.order.venue_id
        }

        response = self._get(query_params, customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(response.json["total_count"], len(results))

        query_params = {
            "venue_id": 99999999
        }

        response = self._get(query_params, customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        self.assertEqual(response.json["total_count"], len(results))

        query_params = {
            "customer_id": Manager.create_customer().user_id
        }

        response = self._get(query_params, customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "search_term": self.order.venue.title
        }

        response = self._get(query_params, customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

    def test_with_company_member(self):
        company_member = Manager.create_company_member(company=self.order.venue.company)

        access_token = Manager.get_access_token(company_member.user)

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

    def test_with_staff(self):
        order = Manager.create_order(customer=self.order.customer)
        order.venue.title = "bunsen--"
        order.venue.save()
        order.status = Constants.ORDER_STATUS_ACCEPTED
        order.save()

        order_2 = Manager.create_order(company=self.order.venue.company)

        staff = Manager.create_staff(venue=self.order.venue)

        access_token = Manager.get_access_token(staff.company_member.user)

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        staff.company_member.active_venue = self.order.venue
        staff.company_member.save()

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["id"], self.order.id)

        self.assertEqual(response.json["total_count"], len(results))

        query_params = {
            "statuses": Constants.ORDER_STATUS_ACCEPTED
        }

        response = self._get(query_params, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params = {
            "statuses": f"{Constants.ORDER_STATUS_ACCEPTED},{Constants.ORDER_STATUS_PENDING}"
        }

        response = self._get(query_params, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "delivery_statuses": Constants.DELIVERY_STATUS_PENDING
        }

        response = self._get(query_params, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        driver = Manager.create_driver()

        query_params = {
            "driver_id": driver.user_id
        }

        response = self._get(query_params, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "customer_id": Manager.create_customer().user_id
        }

        response = self._get(query_params, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "venue_id": order_2.venue.id
        }

        response = self._get(query_params, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "search_term": self.order.venue.title
        }
        response = self._get(query_params, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "search_term": order.venue.title
        }
        response = self._get(query_params, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

    def test_with_company_member_of_different_company(self):
        access_token = Manager.get_company_member_access_token()

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

    def test_with_staff_of_different_company(self):
        access_token = Manager.get_staff_access_token()

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

    def test_with_wrong_status_and_delivery_status(self):
        query_params = {
            "statuses": None
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        query_params = {
            "statuses": "random",
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params = {
            "delivery_statuses": "random",
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params = {
            "delivery_statuses": None
        }

        response = self._get(query_params, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())

