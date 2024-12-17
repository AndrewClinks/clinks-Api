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
        response = super()._post("/delivery-distances", data, access_token)

        return response

    def test_success(self):
        data = Data.valid_delivery_distances_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        results = response.json["delivery_distances"]

        self.assertEqual(len(results), len(data["delivery_distances"]))

    def test_failure_where_driver_fee_bigger_than_delivery_fee(self):
        data = Data.valid_delivery_distances_data()
        data["delivery_distances"][0]["driver_fee"] = 2000

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_distances"][0]["DeliveryDistance"][0], 'driver_fee cannot be bigger than fee' )

    def test_failure_where_starts_greater_than_ends(self):
        data = Data.valid_delivery_distances_data([Data.valid_delivery_distance_data(5, 0)])

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_distances"][0]["DeliveryDistance"][0], "'starts' cannot be bigger than 'ends'")

    def test_failure_where_gaps_between_distances(self):
        data = Data.valid_delivery_distances_data([Data.valid_delivery_distance_data(0, 5), Data.valid_delivery_distance_data(8, 9)])

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["non_field_errors"][0], "1st delivery distance's 'ends' must match 2nd delivery distance's 'starts'")

    def test_failure_where_distance_between_already_existing_distance(self):
        data = Data.valid_delivery_distances_data(
            [Data.valid_delivery_distance_data(0, 5),
             Data.valid_delivery_distance_data(5, 9),
             Data.valid_delivery_distance_data(6, 8)])

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["non_field_errors"][0],
                         "2nd delivery distance's 'ends' must match 3rd delivery distance's 'starts'")

    def test_update_existing_values(self):
        data = Data.valid_delivery_distances_data([Data.valid_delivery_distance_data()])

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(len(response.json["delivery_distances"]), 1)

        id_of_first = response.json["delivery_distances"][0]["id"]

        data = Data.valid_delivery_distances_data()

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(len(response.json["delivery_distances"]), len(data["delivery_distances"]))

        self.assertNotEqual(response.json["delivery_distances"][0]["id"], id_of_first)

    def test_failure_where_first_one_does_not_start_from_zero(self):
        data = Data.valid_delivery_distances_data([Data.valid_delivery_distance_data(2)])

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["non_field_errors"][0], '1st delivery distance should start from 0')

    def test_failure_where_starts_at_and_ends_at_same(self):
        data = Data.valid_delivery_distances_data(
            [Data.valid_delivery_distance_data(0, 0),
             ])

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_distances"][0]["DeliveryDistance"][0], "'starts' cannot be equal to 'ends'")

        data = Data.valid_delivery_distances_data(
            [Data.valid_delivery_distance_data(0, 5),
             Data.valid_delivery_distance_data(5, 5),
             ])

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_distances"][1]["DeliveryDistance"][0], "'starts' cannot be equal to 'ends'")


    def test_failure_with_empty_or_null_list(self):
        response = self._post({}, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_distances"][0], 'This field is required.')

        data = {
            "delivery_distances": {}
        }

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_distances"]["non_field_errors"][0], 'Expected a list of items but got type "dict".')

        data = {
            "delivery_distances": None
        }

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_distances"][0], 'This field may not be null.')

        data = {
            "delivery_distances": []
        }

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["delivery_distances"]["non_field_errors"][0],  'This list may not be empty.')

        data = {
            "delivery_distances": [{}]
        }

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json["delivery_distances"][0]["starts"][0], 'This field is required.')
        self.assertEqual(response.json["delivery_distances"][0]["ends"][0], 'This field is required.')
        self.assertEqual(response.json["delivery_distances"][0]["fee"][0], 'This field is required.')

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._post({}, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._post({}))
