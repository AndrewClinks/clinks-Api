from ...tests.TestCase import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from ..utils import Manager, Data


class DetailTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.order = Manager.create_order()

    def _get(self, id, access_token="", **kwargs):
        response = super()._get(f"/orders/{id}", access_token=access_token)

        return response

    def test_success_with_admin(self):
        response = self._get(self.order.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_success_with_staff(self):
        self.staff = Manager.create_staff(venue=self.order.venue)

        self.member_access_token = Manager.get_access_token(self.staff.company_member.user)

        response = self._get(self.order.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_success_with_customer(self):
        access_token = Manager.get_access_token(self.order.customer.user)

        response = self._get(self.order.id, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json["payment"]["delivery_fee"], Manager.get_delivery_distance_for(0).fee)

    def test_success_with_driver(self):
        driver = Manager.create_driver()
        self.order.driver = driver
        self.order.save()

        access_token = Manager.get_access_token(driver.user)

        response = self._get(self.order.id, access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_failure_with_staff_belongs_to_different_venue_of_same_company(self):
        staff = Manager.create_staff(venue=Manager.create_venue(company=self.order.venue.company))

        access_token = Manager.get_access_token(staff.company_member.user)

        response = self._get(self.order.id, access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_company_member_belongs_to_different_company(self):
        response = self._get(self.order.id, Manager.get_company_member_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_customer(self):
        response = self._get(self.order.id, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_driver(self):
        response = self._get(self.order.id, Manager.get_driver_access_token())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_invalid_id(self):
        response = self._get(9999, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._get(999))
