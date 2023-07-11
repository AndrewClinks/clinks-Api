from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ...utils import Constants, DateUtils
from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _get(self, query_params_dict=None, access_token="", **kwargs):

        response = super()._get("/daily-stats", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        query_params_dict = {
            "total": True,
            "company": True,
            "platform": True,
            "driver": True
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        total_stats = response.json["total"]

        length = len(total_stats)
        self.assertEqual(length, 8)
        self.assertEqual(total_stats[length-1]["date"], str(DateUtils.today().date()))
        self.assertEqual(total_stats[length-1]["sales_count"], 0)
        self.assertEqual(total_stats[length - 1]["earnings"], 0)

        company_stats = response.json["company"]

        length = len(company_stats)
        self.assertEqual(length, 8)
        self.assertEqual(company_stats[length - 1]["date"], str(DateUtils.today().date()))
        self.assertEqual(company_stats[length - 1]["sales_count"], 0)
        self.assertEqual(company_stats[length - 1]["earnings"], 0)

        driver_stats = response.json["driver"]

        length = len(driver_stats)
        self.assertEqual(length, 8)
        self.assertEqual(driver_stats[length - 1]["date"], str(DateUtils.today().date()))
        self.assertEqual(driver_stats[length - 1]["sales_count"], 0)
        self.assertEqual(driver_stats[length - 1]["earnings"], 0)

        platform_stats = response.json["platform"]

        length = len(platform_stats)
        self.assertEqual(length, 8)
        self.assertEqual(platform_stats[length - 1]["date"], str(DateUtils.today().date()))
        self.assertEqual(platform_stats[length - 1]["sales_count"], 0)
        self.assertEqual(platform_stats[length - 1]["earnings"], 0)

        today = DateUtils.today().date()

        order_1 = Manager.create_order(time_to_freeze=f"{today} 12:31:01")
        order_2 = Manager.create_order(time_to_freeze=f"{today} 12:31:01")

        venue = Manager.create_venue()

        query_params_dict = {
            "total": True,
            "company": True,
            "platform": True,
            "driver": True,
            "min_date": str(today),
            "max_date": str(today)
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        total_stats = response.json["total"]

        self.assertEqual(len(total_stats), 1)
        self.assertEqual(total_stats[0]["date"], str(DateUtils.today().date()))
        self.assertEqual(total_stats[0]["sales_count"], 2)
        self.assertEqual(total_stats[0]["earnings"], order_1.payment.total*2)

        platform_stats = response.json["platform"]

        self.assertEqual(len(platform_stats), 1)
        self.assertEqual(platform_stats[0]["date"], str(DateUtils.today().date()))
        self.assertEqual(platform_stats[0]["sales_count"], 2)
        self.assertEqual(platform_stats[0]["earnings"], order_1.payment.service_fee * 2)

        driver_stats = response.json["driver"]

        self.assertEqual(len(driver_stats), 1)
        self.assertEqual(driver_stats[0]["date"], str(DateUtils.today().date()))
        self.assertEqual(driver_stats[0]["sales_count"], 2)
        self.assertEqual(driver_stats[0]["earnings"], (order_1.payment.delivery_driver_fee + order_1.payment.tip) * 2)

        company_stats = response.json["company"]

        self.assertEqual(len(company_stats), 1)
        self.assertEqual(company_stats[0]["date"], str(DateUtils.today().date()))
        self.assertEqual(company_stats[0]["sales_count"], 2)
        self.assertEqual(company_stats[0]["earnings"], order_1.payment.amount * 2)

        query_params_dict = {
            "total": True,
            "company": True,
            "min_date": str(today),
            "max_date": str(today),
            "company_id": order_1.venue.company.id
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company_stats = response.json["company"]

        self.assertEqual(len(company_stats), 1)
        self.assertEqual(company_stats[0]["date"], str(DateUtils.today().date()))
        self.assertEqual(company_stats[0]["sales_count"], 1)
        self.assertEqual(company_stats[0]["earnings"], order_1.payment.amount)

    def test_with_no_query_params(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json, {})

    def test_failure_with_max_date_less_than_min_date(self):
        query_params_dict = {
            "min_date": str(DateUtils.today().date()),
            "max_date": str(DateUtils.yesterday().date())
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "'max_date' cannot be less than 'min_date'")

        query_params_dict = {
            "min_date": str(DateUtils.tomorrow().date())
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "'min_date' cannot be in the future")

        query_params_dict = {
            "max_date": str(DateUtils.days_later(32).date())
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "'max_date' cannot be in the future")

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._get(access_token=Manager.get_company_member_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
