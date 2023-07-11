from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class ListTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.company = Manager.create_company()

        self.company_member_access_token = Manager.get_access_token(self.company.members.first().user)

    def _get(self, query_params_dict=None, access_token="", **kwargs):
        response = super()._get("/stripe-connect", query_params_dict, access_token)

        return response

    def test_with_admin(self):
        self.assertIsNone(self.company.stripe_account_id)

        query_params_dict = {
            "company_id": self.company.id,
            "return_url": "http://127.0.0.1:8000/",
            "refresh_url": "http://127.0.0.1:8000/",
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["connect_url"])

        self.company.refresh_from_db()

        self.assertIsNotNone(self.company.stripe_account_id)

    def test_with_company_member(self):
        self.assertIsNone(self.company.stripe_account_id)

        query_params_dict = {
            "company_id": self.company.id,
            "return_url": "http://127.0.0.1:8000/",
            "refresh_url": "http://127.0.0.1:8000/",
        }

        response = self._get(query_params_dict, self.company_member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["connect_url"])

        self.company.refresh_from_db()

        self.assertIsNotNone(self.company.stripe_account_id)

    def test_failure_without_required_data(self):
        response = self._get(access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'company_id is required.')

        data = {
            "company_id": 1,
        }

        response = self._get(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'return_url is required.')

        data = {
            "company_id": 1,
            "return_url": "return_url"
        }

        response = self._get(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'refresh_url is required.')

    def test_failure_with_company_belongs_to_someone_else(self):
        query_params_dict = {
            "company_id": self.company.id,
            "return_url": "http://127.0.0.1:8000/",
            "refresh_url": "http://127.0.0.1:8000/",
        }

        response = self._get(query_params_dict, Manager.get_company_member_access_token())

        self.company.refresh_from_db()

        self.assertIsNone(self.company.stripe_account_id)

    def test_with_company_with_stripe_account(self):
        company = Manager.create_company()
        company.save()

        query_params_dict = {
            "company_id": company.id,
            "return_url": "http://127.0.0.1:8000/",
            "refresh_url": "http://127.0.0.1:8000/",
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company.refresh_from_db()

        stripe_account_id = company.stripe_account_id

        self.assertIsNotNone(stripe_account_id)

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company.refresh_from_db()

        self.assertEqual(company.stripe_account_id, stripe_account_id)

    def test_failure_with_stripe_connected_and_verified_company(self):
        company = Manager.create_company()
        company.stripe_account_id = 9999
        company.stripe_verification_status = "verified"
        company.save()

        query_params_dict = {
            "company_id": company.id,
            "return_url": "http://127.0.0.1:8000/",
            "refresh_url": "http://127.0.0.1:8000/",
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'This company is already connected to stripe.')

    def test_with_invalid_id(self):
        query_params_dict = {
            "company_id": 9999,
            "return_url": "http://127.0.0.1:8000/",
            "refresh_url": "http://127.0.0.1:8000/",
        }

        response = self._get(query_params_dict, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], 'Company with this id does not exist')

    def test_failure_with_customer(self):
        self.permission_denied_test(self._get(access_token=Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._get(access_token=Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get())
