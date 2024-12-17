from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...delivery_request.models import DeliveryRequest

from ...utils import Constants
from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/delivery-requests", query_params_dict, access_token)
        return response

    def test_success(self):
        driver = Manager.create_driver()

        driver_access_token = Manager.get_access_token(driver.user)

        order = Manager.get_order_looking_for_driver_with_close_driver(driver=driver)

        response = self._get(access_token=driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["driver"], driver.user_id)

        self.assertEqual(results[0]["order"]["id"], order.id)

        self.assertIsNotNone(results[0]["order"]["data"]["customer_address"])

        self.assertIsNotNone(results[0]["order"]["data"]["venue_address"])

    def test_filter(self):
        driver = Manager.create_driver()

        driver_access_token = Manager.get_access_token(driver.user)

        order_1 = Manager.get_order_looking_for_driver_with_close_driver(driver=driver)
        order_2 = Manager.get_order_looking_for_driver_with_close_driver(driver=driver)
        order_3 = Manager.get_order_looking_for_driver_with_close_driver(driver=driver)
        order_4 = Manager.get_order_looking_for_driver_with_close_driver(driver=driver)

        response = self._get(access_token=driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 4)

        self.assertEqual(results[0]["order"]["id"], order_1.id)

        delivery_request = DeliveryRequest.objects.get(id=results[0]["id"])
        delivery_request.status = Constants.DELIVERY_REQUEST_STATUS_MISSED
        delivery_request.save()

        response = self._get(access_token=driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["order"]["id"], order_2.id)

        query_params_dict = {
            "status": Constants.DELIVERY_REQUEST_STATUS_ACCEPTED
        }

        response = self._get(query_params_dict, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 0)

        query_params_dict = {
            "last_rejected_order_id": order_2.id
        }

        response = self._get(query_params_dict, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["order"]["id"], order_3.id)

        query_params_dict = {
            "last_rejected_order_id": order_3.id
        }

        response = self._get(query_params_dict, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["order"]["id"], order_4.id)

        driver_2 = Manager.create_driver()

        driver_access_token_2 = Manager.get_access_token(driver_2.user)

        order_5 = Manager.get_order_looking_for_driver_with_close_driver(driver=driver_2)

        response = self._get(access_token=driver_access_token_2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["order"]["id"], order_5.id)

    def test_with_invalid_query_params(self):
        driver = Manager.create_driver()

        driver_access_token = Manager.get_access_token(driver.user)

        order = Manager.get_order_looking_for_driver_with_close_driver(driver=driver)

        query_params_dict = {
            "status": None
        }

        response = self._get(query_params_dict, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["results"][0]["status"], Constants.DELIVERY_REQUEST_STATUS_PENDING)

        query_params_dict = {
            "status": Constants.DELIVERY_REQUEST_STATUS_EXPIRED
        }

        response = self._get(query_params_dict, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["results"][0]["status"], Constants.DELIVERY_REQUEST_STATUS_PENDING)

        query_params_dict = {
            "last_rejected_order_id": None
        }

        response = self._get(query_params_dict, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 1)

        query_params_dict = {
            "last_rejected_order_id": 9999
        }

        response = self._get(query_params_dict, driver_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 0)

    def test_with_driver_without_any_delivery_requests(self):
        access_token = Manager.get_driver_access_token()

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 0)

        query_params_dict = {
            "last_rejected_order_id": 1
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json["results"]), 0)

    def test_failure_with_admin(self):
        self.permission_denied_test(self._get(access_token=Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(access_token=Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
