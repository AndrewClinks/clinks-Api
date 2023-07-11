from rest_framework.test import APIClient
from rest_framework import status

from ...all_time_stat.models import AllTimeStat
from ...company.models import Company

from ...tests.TestCase import TestCase

from ..utils import Data, Manager

from ...utils import Constants


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.company = Manager.create_company()

        self.member = self.company.members.first()

        self.member_access_token = Manager.get_access_token(self.member.user)

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/venues", data, access_token)

        return response

    def test_success_with_admin(self):
        count_of_venues = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_VENUE_COUNT)

        opening_hours_data = [Data.valid_opening_hour("sunday"), Data.valid_opening_hour("monday")]

        data = Data.valid_venue_data(opening_hours=opening_hours_data)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIsNotNone(response.json["company"])
        self.assertEqual(len(response.json["opening_hours"]), len(opening_hours_data))
        self.assertEqual(response.json["opening_hours"][0]["day"], "monday")
        self.assertEqual(response.json["opening_hours"][1]["day"], "sunday")

        self.assertEqual(Company.objects.filter(id=response.json["company"]["id"]).first().venue_count, 1)
        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_VENUE_COUNT), count_of_venues+1)

    def test_success_with_company_member(self):
        count_of_venues = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_VENUE_COUNT)
        count_of_company_venues = self.company.venue_count

        data = Data.valid_venue_data(self.company)

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.company.refresh_from_db()

        self.assertEqual(self.company.venue_count, count_of_company_venues+1)
        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_VENUE_COUNT), count_of_venues+1)
        self.assertEqual(response.json["company"]["id"], self.company.id)

    def test_with_company_belongs_to_someone_else(self):
        data = Data.valid_venue_data()
        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["company"]["id"], self.company.id)

    def test_failure_without_required_fields(self):
        data = {}

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["title"][0], 'This field is required.')
        self.assertEqual(response.json["address"][0], 'This field is required.')
        self.assertEqual(response.json["company"][0], 'This field is required.')
        self.assertEqual(response.json["phone_country_code"][0], 'This field is required.')
        self.assertEqual(response.json["phone_number"][0], 'This field is required.')
        self.assertEqual(response.json["opening_hours"][0], 'This field is required.')

        data = Data.valid_venue_data()

        data.update({
            "address": {},
            "opening_hours": {}
        })

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["address"]["latitude"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["longitude"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["line_1"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["city"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["country"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["state"][0], 'This field is required.')
        self.assertEqual(response.json["address"]["country_short"][0], 'This field is required.')
        self.assertEqual(response.json["opening_hours"]["non_field_errors"][0], 'Expected a list of items but got type "dict".')

        data.update({
            "address": Data.valid_address_data(),
            "opening_hours": [{}]
        })

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["opening_hours"][0]["day"][0], 'This field is required.')
        self.assertEqual(response.json["opening_hours"][0]["starts_at"][0], 'This field is required.')
        self.assertEqual(response.json["opening_hours"][0]["ends_at"][0], 'This field is required.')

    def test_with_repeated_days(self):

        opening_hours = [
            Data.valid_opening_hour(),
            Data.valid_opening_hour()
        ]

        data = Data.valid_venue_data(opening_hours=opening_hours)

        response = self._post(data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(len(response.json["opening_hours"]), 1)

    def test_failure_when_opening_hour_starts_bigger_than_ends(self):
        opening_hours = [Data.valid_opening_hour(starts_at="2:00", ends_at="1:00")]

        data = Data.valid_venue_data(opening_hours=opening_hours)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["opening_hours"][0]["Time"][0], "'starts_at' cannot be later than 'ends_at'")

    def test_failure_opening_hour_incorrect_day(self):
        opening_hours = [Data.valid_opening_hour("xy")]

        data = Data.valid_venue_data(opening_hours=opening_hours)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["opening_hours"][0]["Day"][0], "'day' needs to be one of ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']")

    def test_failure_opening_hour_starts_at_equals_to_ends_at(self):
        opening_hours = [Data.valid_opening_hour(starts_at="10:00", ends_at="10:00")]

        data = Data.valid_venue_data(opening_hours=opening_hours)

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["opening_hours"][0]["Time"][0], "'starts_at' and 'ends_at' cannot be same")

    def test_failure_with_non_existing_company(self):
        data = Data.valid_venue_data()
        data["company"] = 12344234

        response = self._post(data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["company"][0], 'Invalid pk "12344234" - object does not exist.')

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_customer(self):
        self.permission_denied_test(self._post({}, Manager.get_customer_access_token()))

    def test_failure_with_unauthorized(self):
        self.permission_denied_test(self._post({}))
