from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...company.models import Company

from ...utils import Constants


class EditTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.company = Manager.create_company()

        self.member = self.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

        self.venue = Manager.create_venue(self.company)

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/venues/{id}", data, access_token)

        return response

    def test_with_admin(self):
        data = {
            "title": "title",
            "phone_country_code": "+353",
            "phone_number": "987654321",
            "address": Data.valid_address_data("line_1"),
            "description": "description2",
            "opening_hours": [Data.valid_opening_hour("wednesday")]
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["title"], data["title"])
        self.assertEqual(response.json["address"]["line_1"], data["address"]["line_1"])
        self.assertEqual(response.json["phone_country_code"], data["phone_country_code"])
        self.assertEqual(response.json["phone_number"], data["phone_number"])
        self.assertEqual(response.json["description"], data["description"])

        opening_hours = response.json["opening_hours"]

        self.assertEqual(len(opening_hours), len(data["opening_hours"]))

        opening_hours.append(Data.valid_opening_hour(day="tuesday"))

        data = {
            "opening_hours": opening_hours
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        opening_hours = response.json["opening_hours"]

        self.assertEqual(len(opening_hours), len(data["opening_hours"]))
        self.assertEqual(opening_hours[0]["day"], "tuesday")

        data = {
            "opening_hours": []
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        opening_hours = response.json["opening_hours"]

        self.assertEqual(len(opening_hours), 0)

    def test_with_company_member(self):
        data = {
            "title": "title",
            "phone_country_code": "+353",
            "phone_number": "987654321",
            "address": Data.valid_address_data("line_1"),
            "description": "description2",
            "opening_hours": [Data.valid_opening_hour("wednesday")]
        }

        response = self._patch(self.venue.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["title"], data["title"])
        self.assertEqual(response.json["address"]["line_1"], data["address"]["line_1"])
        self.assertEqual(response.json["phone_country_code"], data["phone_country_code"])
        self.assertEqual(response.json["phone_number"], data["phone_number"])
        self.assertEqual(response.json["description"], data["description"])

        opening_hours = response.json["opening_hours"]

        self.assertEqual(len(opening_hours), len(data["opening_hours"]))

    def test_update_paused_field(self):
        response = self._patch(self.venue.id, {"paused": True}, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["paused"], True)

        response = self._patch(self.venue.id, {"paused": False}, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["paused"], False)

    def test_failure_without_required_fields(self):
        data = {
            "title": None,
            "phone_country_code": None,
            "phone_number": None,
            "address": None,
            "description": None,
            "opening_hours": None
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["title"][0], 'This field may not be null.')
        self.assertEqual(response.json["address"][0], 'This field may not be null.')
        self.assertEqual(response.json["phone_country_code"][0], 'This field may not be null.')
        self.assertEqual(response.json["phone_number"][0], 'This field may not be null.')
        self.assertEqual(response.json["opening_hours"][0], 'This field may not be null.')

        data = {
            "address": {},
            "opening_hours": []
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["address"]["latitude"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["longitude"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["line_1"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["city"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["country"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["state"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["country_short"][0], 'This field is required.')

        data = {
            "opening_hours": [{}]
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["opening_hours"][0]["day"][0], 'This field is required.')
        self.assertEqual(response.json["opening_hours"][0]["starts_at"][0], 'This field is required.')
        self.assertEqual(response.json["opening_hours"][0]["ends_at"][0], 'This field is required.')

    def test_with_repeated_days(self):
        opening_hours_data = [Data.valid_opening_hour("wednesday", starts_at="1:00", ends_at="2:00")]

        data = {
            "opening_hours": opening_hours_data
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        opening_hours = response.json["opening_hours"]
        opening_hours.append(Data.valid_opening_hour("wednesday", starts_at="2:00", ends_at="3:00"))

        id_of_first_item = opening_hours[0]["id"]

        data = {
            "opening_hours": opening_hours
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        opening_hours = response.json["opening_hours"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(opening_hours), 1)

        self.assertEqual(opening_hours[0]["id"], id_of_first_item)
        self.assertEqual(opening_hours[0]["starts_at"], "01:00:00")
        self.assertEqual(opening_hours[0]["ends_at"], "02:00:00")

    def test_failure_when_opening_hour_starts_bigger_than_ends(self):
        opening_hours = [Data.valid_opening_hour(starts_at="2:00", ends_at="1:00")]

        data = {
            "opening_hours": opening_hours
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["opening_hours"][0]["Time"][0], "'starts_at' cannot be later than 'ends_at'")

    def test_failure_opening_hour_incorrect_day(self):
        opening_hours = [Data.valid_opening_hour("xy")]

        data = {
            "opening_hours": opening_hours
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["opening_hours"][0]["Day"][0],
                         "'day' needs to be one of ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']")

    def test_failure_opening_hour_starts_at_equals_to_ends_at(self):
        opening_hours = [Data.valid_opening_hour(starts_at="10:00", ends_at="10:00")]

        data = {
            "opening_hours": opening_hours
        }

        response = self._patch(self.venue.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["opening_hours"][0]["Time"][0], "'starts_at' and 'ends_at' cannot be same")


    def test_failure_with_non_existing_company(self):
        response = self._patch(999, {}, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_venue_belongs_to_someone_else(self):
        venue = Manager.create_venue()

        response = self._patch(venue.id, {}, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_customer(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.permission_denied_test(self._patch(999, {}))