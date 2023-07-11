from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Data, Manager

from ...utils import Api

import json

# todo
class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.company = Manager.create_company()

    def _create(self, data):
        response = super()._post("/webhooks/stripe", data)

        return response

    def _test_create(self):
        data = Data.valid_webhook_data()

        self.company.stripe_account_id = data["account"]
        self.company.save()

        self.assertFalse(self.company.stripe_charges_enabled)

        response = self._create(data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["status"], "success")

        self.company.refresh_from_db()

        self.assertTrue(self.company.stripe_charges_enabled)

    def _test_failure_with_missing_params(self):
        data = Data.valid_webhook_data()

        del data["id"]

        response = self._create(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = json.loads(response.content)

        self.assertEqual(json_response["detail"], "Invalid event data, missing \'id\' or \'account\'")

        data = Data.valid_webhook_data()

        del data["account"]

        response = self._create(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = json.loads(response.content)

        self.assertEqual(json_response["detail"], "Invalid event data, missing \'id\' or \'account\'")

    def _test_failure_invalid_stripe_account(self):
        data = Data.valid_webhook_data()

        response = self._create(data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        json_response = json.loads(response.content)

        self.assertEqual(json_response["detail"], "Not found.")

    def _test_failure_with_invalid_account_id(self):
        data = Data.valid_webhook_data()

        data["account"] = "222"

        response = self._create(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = json.loads(response.content)

        self.assertEqual(json_response["detail"], "Invalid event data, no such event")

    def _test_failure_duplicate_event(self):
        data = Data.valid_webhook_data()

        self.company.stripe_account_id = data["account"]
        self.company.save()

        response = self._create(data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = json.loads(response.content)

        self.assertEqual(json_response["status"], "success")

        response = self._create(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = json.loads(response.content)

        self.assertEqual(json_response["event_id"], "Duplicate event")
