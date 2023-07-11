from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...utils import Constants

from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/payments", query_params_dict, access_token)

        return response

    def test_success(self):
        order_delivered = Manager.create_delivered_order()
        order_delivered.venue.company.title = "xyz"
        order_delivered.venue.company.save()

        order_rejected = Manager.create_rejected_order()
        order_rejected.customer.user.first_name = "abc"
        order_rejected.customer.user.save()

        order_returned = Manager.create_returned_order()

        response = self._get(access_token=self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 3)

        query_params_dict = {
            "search_term": order_delivered.venue.company.title,
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 1)

        self.assertEqual(response.json["results"][0]["id"], order_delivered.payment.id)

        query_params_dict = {
            "search_term": "abc",
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 1)

        self.assertEqual(response.json["results"][0]["id"], order_rejected.payment.id)

        query_params_dict = {
            "order_status": Constants.ORDER_STATUS_REJECTED
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 1)

        self.assertEqual(response.json["results"][0]["id"], order_rejected.payment.id)

        query_params_dict = {
            "order_status": Constants.ORDER_STATUS_ACCEPTED
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 2)

        query_params_dict = {
            "order_status": Constants.ORDER_STATUS_PENDING
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 3)

        query_params_dict = {
            "delivery_status": Constants.DELIVERY_STATUS_DELIVERED
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 1)

        self.assertEqual(response.json["results"][0]["id"], order_delivered.payment.id)

        query_params_dict = {
            "delivery_status": Constants.DELIVERY_STATUS_RETURNED
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 1)

        self.assertEqual(response.json["results"][0]["id"], order_returned.payment.id)

        query_params_dict = {
            "delivery_status": Constants.DELIVERY_STATUS_PENDING
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 3)


    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(access_token=Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
