from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/categories", data, access_token)

        return response

    def test_with_admin(self):
        data = Data.valid_category_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["title"], data["title"])
        self.assertEqual(response.json["sales_count"], 0)
        self.assertEqual(response.json["image"], data["image"])
        self.assertIsNone(response.json["parent"])

    def test_with_parent(self):
        category = Manager.create_category()

        data = Data.valid_category_data(parent=category)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.json["parent"], category.id)

        data = Data.valid_category_data(parent=category)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.json["parent"], category.id)

        data = Data.valid_category_data()

        response = self._post(data, self.admin_access_token)

        self.assertIsNone(response.json["parent"])

    def test_with_same_title(self):
        category = Manager.create_category()

        data = Data.valid_category_data(title=category.title)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["id"], category.id)

        data["title"] = category.title.upper()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["id"], category.id)

        data["parent"] = category.id

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertNotEqual(response.json["id"], category.id)

        subcategory_id = response.json["id"]

        data = Data.valid_category_data(title=category.title, parent=category)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["id"], subcategory_id)

    def test_with_using_title_of_deleted_category(self):
        category = Manager.create_category()
        response = super()._delete(f"/categories/{category.id}", access_token=self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        data = Data.valid_category_data(title=category.title)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertNotEqual(response.json["id"], category.id)

    def test_failure_without_required_data(self):
        response = self._post({}, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["title"][0], 'This field is required.')
        self.assertEqual(response.json["image"][0], 'This field is required.')

        data = Data.valid_category_data()
        data["image"] = Manager.create_category().image.id

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["image"][0], 'This field must be unique.')

    def test_failure_with_invalid_parent_and_image_id(self):
        data = Data.valid_category_data()
        data["parent"] = 999
        data["image"] = 9999

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["parent"][0], 'Invalid pk "999" - object does not exist.')
        self.assertEqual(response.json["image"][0], 'Invalid pk "9999" - object does not exist.')

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._post({}, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.permission_denied_test(self._post({}))
