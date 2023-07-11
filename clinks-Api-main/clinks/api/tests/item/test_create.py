from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...category.models import Category

from ...utils import DateUtils


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/items", data, access_token)

        return response

    def test_success(self):
        data = Data.valid_item_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["image"]["id"], data["image"])
        self.assertEqual(response.json["title"], data["title"])
        self.assertEqual(response.json["description"], data["description"])
        self.assertEqual(response.json["sales_count"], 0)
        self.assertEqual(response.json["subcategory"]["id"], data["subcategory"])

        subcategory = Category.objects.get(id=response.json["subcategory"]["id"])

        self.assertEqual(subcategory.item_count, 1)
        self.assertEqual(subcategory.parent.item_count, 1)

        subcategory_id = response.json["subcategory"]["id"]

        data = Data.valid_item_data()
        data["subcategory"] = subcategory_id

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        subcategory.refresh_from_db()

        self.assertEqual(subcategory.item_count, 2)
        self.assertEqual(subcategory.parent.item_count, 2)

        subcategory_data = Data.valid_category_data()
        subcategory_data["parent"] = subcategory.parent_id
        new_subcategory_from_same_parent = Manager.create_subcategory(subcategory_data)

        data = Data.valid_item_data(subcategory=new_subcategory_from_same_parent)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        subcategory.refresh_from_db()

        self.assertEqual(subcategory.item_count, 2)
        self.assertEqual(subcategory.parent.item_count, 3)

        subcategory = Category.objects.get(id=response.json["subcategory"]["id"])

        self.assertEqual(subcategory.item_count, 1)

        data = Data.valid_item_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        subcategory = Category.objects.get(id=response.json["subcategory"]["id"])

        self.assertEqual(subcategory.item_count, 1)
        self.assertEqual(subcategory.parent.item_count, 1)

    def test_failure_with_using_category_instead_of_subcategory(self):
        data = Data.valid_item_data(subcategory=Manager.create_category())

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["subcategory"]["Subcategory"], 'It has to be a subcategory')

    def test_failure_with_using_image_belongs_to_different_item(self):
        item = Manager.create_item()

        data = Data.valid_item_data(image=item.image)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["image"][0], 'This field must be unique.')

    def test_with_same_title(self):
        item = Manager.create_item()

        data = Data.valid_item_data(title=item.title)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["id"], item.id)
        self.assertEqual(response.json["title"], item.title)

        data = Data.valid_item_data(title=item.title.upper())

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["id"], item.id)
        self.assertEqual(response.json["title"], item.title)

    def test_failure_with_invalid_subcategory_and_image_ids(self):
        data = Data.valid_item_data()
        data["subcategory"] = 99999
        data["image"] = 999999

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["image"][0], 'Invalid pk "999999" - object does not exist.')
        self.assertEqual(response.json["subcategory"][0], 'Invalid pk "99999" - object does not exist.')

    def test_failure_without_required_info(self):
        response = self._post({}, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["title"][0], 'This field is required.')
        self.assertEqual(response.json["image"][0], 'This field is required.')
        self.assertEqual(response.json["subcategory"][0], 'This field is required.')

        data = {
            "title": None,
            "image": None,
            "subcategory": None
        }

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["title"][0], 'This field may not be null.')
        self.assertEqual(response.json["image"][0], 'This field may not be null.')
        self.assertEqual(response.json["subcategory"][0], 'This field may not be null.')

    def test_failure_with_deleted_subcategory(self):
        subcategory = Manager.create_subcategory()
        subcategory.deleted_at = DateUtils.now()
        subcategory.save()

        data = Data.valid_item_data(subcategory=subcategory)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(" object does not exist" in response.json["subcategory"][0])

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._post({}, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.permission_denied_test(self._post({}))
