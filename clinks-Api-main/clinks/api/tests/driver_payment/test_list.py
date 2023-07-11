from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...driver_payment.models import DriverPayment

from ...utils import Constants, DateUtils

from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/driver-payments", query_params_dict, access_token)

        return response

    def test_success(self):
        order_delivered = Manager.create_delivered_order()
        order_delivered.driver.user.first_name = "abc"
        order_delivered.driver.user.save()

        order_returned = Manager.create_returned_order()

        response = self._get(access_token=self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 3)

        query_params_dict = {
            "search_term": "abc",
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 1)

        self.assertEqual(response.json["results"][0]["order"], order_delivered.id)

        query_params_dict = {
            "type": Constants.DRIVER_PAYMENT_TYPE_DELIVERY
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 2)

        self.assertEqual(response.json["results"][0]["order"], order_returned.id)
        self.assertEqual(response.json["results"][0]["order"], order_returned.id)

        query_params_dict = {
            "type": Constants.DRIVER_PAYMENT_TYPE_RETURN
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 1)

        self.assertEqual(response.json["results"][0]["order"], order_returned.id)

        query_params_dict = {
            "type": "random"
        }

        response = self._get(query_params_dict, self.admin_access_token)

        results = response.json["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results), 3)

    def test_with_driver(self):
        driver = Manager.create_driver()

        access_token = Manager.get_access_token(driver.user)

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["count"], 0)
        self.assertIsNone(response.json["total_earnings"])
        self.assertIsNone(response.json["total_tips"])

        Manager.create_delivered_order()

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["count"], 0)
        self.assertIsNone(response.json["total_earnings"])
        self.assertIsNone(response.json["total_tips"])

        Manager.create_delivered_order(driver=driver)

        response = self._get(access_token=access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["count"], 1)
        self.assertEqual(response.json["total_earnings"], 800)
        self.assertEqual(response.json["total_tips"], 0)
        self.assertIsNotNone(response.json["currency"])

        query_params_dict = {
            "max_date": str(DateUtils.today().date())
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["count"], 0)
        self.assertIsNone(response.json["total_earnings"])
        self.assertIsNone(response.json["total_tips"])
        self.assertIsNone(response.json["currency"])

        query_params_dict = {
            "min_date": str(DateUtils.today().date())
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["count"], 1)
        self.assertEqual(response.json["total_earnings"], 800)
        self.assertEqual(response.json["total_tips"], 0)
        self.assertIsNotNone(response.json["currency"])

        query_params_dict = {
            "min_date": str(DateUtils.tomorrow().date())
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["count"], 0)
        self.assertIsNone(response.json["total_earnings"])
        self.assertIsNone(response.json["total_tips"])
        self.assertIsNone(response.json["currency"])

        query_params_dict = {
            "min_date": str(DateUtils.yesterday().date()),
            "max_date": str(DateUtils.tomorrow().date())
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["count"], 1)
        self.assertEqual(response.json["total_earnings"], 800)
        self.assertEqual(response.json["total_tips"], 0)
        self.assertIsNotNone(response.json["currency"])

        order = Manager.create_delivered_order(driver=driver)
        driver_payment = DriverPayment.objects.get(order=order)
        driver_payment.created_at = DateUtils.tomorrow().date()
        driver_payment.save()

        query_params_dict = {
            "min_date": str(DateUtils.yesterday().date()),
            "max_date": str(DateUtils.tomorrow().date())
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["count"], 2)
        self.assertEqual(response.json["total_earnings"], 1600)
        self.assertEqual(response.json["total_tips"], 0)
        self.assertIsNotNone(response.json["currency"])

        query_params_dict = {
            "min_date": str(DateUtils.today().date()),
            "max_date": str(DateUtils.yesterday().date())
        }

        response = self._get(query_params_dict, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["count"], 0)
        self.assertIsNone(response.json["total_earnings"])
        self.assertIsNone(response.json["total_tips"])
        self.assertIsNone(response.json["currency"])

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(access_token=Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
