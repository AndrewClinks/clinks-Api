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

    def _patch(self, id, data, access_token="", **kwargs):
        response = super()._patch(f"/companies/{id}", data, access_token)

        return response

    def test_with_admin(self):
        data = {
            "title": "new title",
            "eircode": "eircode2",
            "vat_no": "vat_no2",
            "members": [Data.valid_company_member_data()],
            "logo": Manager.create_image(self.admin_access_token, mock=False).id,
            "featured_image": Manager.create_image(self.admin_access_token).id
        }

        response = self._patch(self.company.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["title"], data["title"])
        self.assertEqual(response.json["eircode"], data["eircode"])
        self.assertEqual(response.json["vat_no"], data["vat_no"])
        self.assertEqual(response.json["logo"]["id"], data["logo"])
        self.assertEqual(response.json["featured_image"]["id"], data["featured_image"])

        members = Company.objects.get(id=response.json["id"]).members

        self.assertEqual(members.count(), 1)

        self.assertEqual(members.first().user_id, self.company.members.first().user_id)

    def test_with_company_member(self):
        data = {
            "title": "new title",
            "eircode": "eircode2",
            "vat_no": "vat_no2",
            "members": [Data.valid_company_member_data()],
            "logo": Manager.create_image(self.member_access_token, mock=False).id,
            "featured_image": Manager.create_image(self.member_access_token).id
        }

        response = self._patch(self.company.id, data, self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["title"], data["title"])

        self.company.refresh_from_db()

        self.assertNotEqual(self.company.eircode, data["eircode"])
        self.assertNotEqual(self.company.vat_no, data["vat_no"])
        self.assertEqual(response.json["logo"]["id"], data["logo"])
        self.assertEqual(response.json["featured_image"]["id"], data["featured_image"])

        members = Company.objects.get(id=response.json["id"]).members

        self.assertEqual(members.count(), 1)

        self.assertEqual(members.first().user_id, self.company.members.first().user_id)


    def test_with_changing_status(self):
        data = {
            "status": Constants.COMPANY_STATUS_PAUSED
        }

        response = self._patch(self.company.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Company"][0], 'status cannot be changed while company is in setup stage')


    def test_failure_with_setting_non_nullable_fields_to_none(self):
        data = {
            "title": None,
            "members": None,
            "featured_image": None,
            "logo": None,
            "eircode": None,
            "vat_no": None,
            "liquor_license_no": None
        }

        response = self._patch(self.company.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["title"][0], 'This field may not be null.')
        self.assertEqual(response.json["eircode"][0], 'This field may not be null.')
        self.assertEqual(response.json["vat_no"][0], 'This field may not be null.')
        self.assertEqual(response.json["liquor_license_no"][0], 'This field may not be null.')

    def test_failure_with_changing_status_to_setup_not_completed(self):
        data = {
            "status": Constants.COMPANY_STATUS_SETUP_NOT_COMPLETED
        }

        response = self._patch(self.company.id, data, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["status"]["status"], "'status needs to be one of ['active', 'paused']'")

    def test_with_company_belongs_to_someone_else(self):
        response = self._patch(self.company.id, {}, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotEqual(response.json["id"], self.company.id)

    def test_failure_adding_image_belongs_to_other_company(self):
        data = {
            "logo": self.company.logo.id
        }

        response = self._patch(self.company.id, data, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["logo"][0], 'This field must be unique.')

    def test_failure_with_non_existing_id(self):
        response = self._patch(999, {}, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_customer(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._patch(999, {}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._patch(999, {}))