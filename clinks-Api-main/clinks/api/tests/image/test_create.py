import uuid

from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Data, Manager


class AuthTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer_access_token = Manager.get_customer_access_token()

    def _post(self, file_name="identification.jpeg", access_token="", **kwargs):
        file = open(f"api/tests/utils/files/{file_name}", 'rb')

        data = {
            "file": file
        }

        response = super()._post("/images", data, access_token, True)

        return response

    def test_success(self):
        response = self._post(access_token=self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue("thumbnail" in response.json)
        self.assertTrue("banner" in response.json)
        self.assertTrue("original" in response.json)

    def test_failure_without_required_data(self):
        response = super()._post("/images", {}, self.customer_access_token, True)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["file"][0], 'No file was submitted.')

    def test_failure_with_unauthorized_account(self):
        response = self._post()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(response.json["detail"], 'Authentication credentials were not provided.')
