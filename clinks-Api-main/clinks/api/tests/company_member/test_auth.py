import uuid

from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status
from ...utils import Constants
from ..utils import Data, Manager


class AuthTest(TestCase):

    client = APIClient()

    def setUp(self):
        member_data = Data.valid_company_member_data(email=Data.TEST_EMAIL)

        self.email = member_data["user"]["email"]
        self.password = member_data["user"]["password"]

        self.member = Manager.create_company_member(member_data)
        self.member_access_token = Manager.get_access_token(self.member.user)

    def test_login(self):
        response = Manager.login(self.email, self.password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("company_member" in response.json)
        self.assertTrue("tokens" in response.json)

        self.assertIsNotNone(response.json["company_member"]["company"]["id"])

        data = Data.valid_company_data()
        Manager.create_company(data)

        user = data["members"][0]["user"]
        response = Manager.login(user["email"], user["password"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("company_member" in response.json)
        self.assertTrue("tokens" in response.json)

    def test_login_after_password_change(self):
        new_password = "89032Aa)"

        updated_login_data = {
            "user": {
                "password": new_password,
                "current_password": self.password
            }
        }

        response = super()._patch(f"/company-members/{self.member.user.id}", updated_login_data,
                                  self.member_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = Manager.login(self.email, new_password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("company_member" in response.json)

        self.assertTrue("tokens" in response.json)

    def test_login_when_current_member_is_second_member(self):
        data = Data.valid_company_member_data()

        Manager.create_company_member(data, self.member.company)

        response = Manager.login(self.email, self.password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("company_member" in response.json)
        self.assertTrue("tokens" in response.json)

    def test_login_after_company_set_to_paused(self):
        super()._patch(f"/companies/{self.member.company.id}", {"status": Constants.COMPANY_STATUSES},
                       Manager.get_admin_access_token())

        response = Manager.login(self.email, self.password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue("company_member" in response.json)
        self.assertTrue("tokens" in response.json)