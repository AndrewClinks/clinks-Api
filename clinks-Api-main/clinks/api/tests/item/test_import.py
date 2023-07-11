from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager
from ...item.models import Item
from ...job.models import Job

import json


class ImportTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin = Manager.create_admin(data=Data.valid_admin_data("a@bc.ie"))
        self.admin_access_token = Manager.get_access_token(self.admin.user)

        self.category_beer = Manager.create_category(Data.valid_category_data(title="Beer"))

        self.subcategory_lager = Manager.create_category(Data.valid_category_data(title="Lager", parent=self.category_beer))

    def _post(self, file_name, access_token="", **kwargs):
        file = open(f"api/tests/utils/files/{file_name}", 'rb')

        data = {
            "csv": file
        }

        response = super()._post("/items/import", data, access_token, True)

        return response

    def test_success(self):
        response = self._post("items_success.csv", self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        items = Item.objects.all()
        job = Job.objects.first()

        self.assertEqual(len(items), 2)
        self.assertIsNone(job.errors)

        first = items.first()
        second = items.last()

        self.assertEqual(first.title, "Heineken 20 X 330Ml Cans")
        self.assertEqual(first.description, "Heineken's unique recipe combines pure malt with hops")
        self.assertEqual(first.subcategory.id, self.subcategory_lager.id)
        self.assertIsNotNone(first.image)

        self.assertEqual(second.title, "Heineken Light 4 Pack 50Cl Can")
        self.assertEqual(second.description, "")
        self.assertEqual(second.subcategory.id, self.subcategory_lager.id)
        self.assertIsNotNone(second.image)

    def test_failure_with_invalid_values(self):
        response = self._post("items_with_invalid_values.csv", self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        items = Item.objects.all()
        job = Job.objects.first()

        skipped_rows = json.loads(job.errors)["skipped_rows"]

        first = items.first()
        second = items.last()

        self.assertEqual(len(items), 2)

        self.assertEqual(first.title, "row 4")
        self.assertEqual(second.title, "row 5")

        self.assertTrue(self.subcategory_lager.image.original in first.image.original)
        self.assertTrue(self.subcategory_lager.image.original in second.image.original)

        self.assertEqual(skipped_rows[0]["row"], 2)
        self.assertEqual(skipped_rows[0]["reason"], "'title' is empty")

        self.assertEqual(skipped_rows[1]["row"], 3)
        self.assertEqual(skipped_rows[1]["reason"], "'title' is empty")

        self.assertEqual(skipped_rows[2]["row"], 6)
        self.assertEqual(skipped_rows[2]["reason"], "there is an issue with the image")

        self.assertEqual(skipped_rows[3]["row"], 7)
        self.assertEqual(skipped_rows[3]["reason"], "there is an issue with the image")

        self.assertEqual(skipped_rows[4]["row"], 8)
        self.assertEqual(skipped_rows[4]["reason"], "'category' is empty")

        self.assertEqual(skipped_rows[5]["row"], 9)
        self.assertEqual(skipped_rows[5]["reason"], "'category' is empty")

        self.assertEqual(skipped_rows[6]["row"], 10)
        self.assertEqual(skipped_rows[6]["reason"], "'subcategory' is empty")

        self.assertEqual(skipped_rows[7]["row"], 11)
        self.assertEqual(skipped_rows[7]["reason"], "'subcategory' is empty")

        self.assertEqual(skipped_rows[8]["row"], 12)
        self.assertEqual(skipped_rows[8]["reason"], "'title' is empty")

        self.assertEqual(skipped_rows[9]["row"], 13)
        self.assertEqual(skipped_rows[9]["reason"], "category: Beer1 doesn't exist")

        self.assertEqual(skipped_rows[10]["row"], 14)
        self.assertEqual(skipped_rows[10]["reason"], "subcategory: Lager1 doesn't exist or belongs to different category")

        self.assertEqual(skipped_rows[11]["row"], 15)
        self.assertEqual(skipped_rows[11]["reason"], "Item with this title: row 4 already exists")

    def test_with_missing_columns(self):
        response = self._post("items_with_missing_columns.csv", self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"], "File is missing 'Description' column")

    def test_failure_with_incorrect_file_types(self):
        response = self._post("b.xlsx", self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"],  "File type is not 'csv'")

        response = self._post("identification.jpeg", self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["detail"],  "File type is not 'csv'")

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._post("items_success.csv", Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post("items_success.csv", Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post("items_success.csv", Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._post("items_success.csv"))
