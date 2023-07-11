from rest_framework.test import APIClient
from rest_framework import status

from ...tests.TestCase import TestCase

from ...all_time_stat.models import AllTimeStat

from ..utils import Data, Manager

from ...utils import Constants


class DeleteTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.admin_access_token = Manager.get_admin_access_token()

        self.driver = Manager.create_driver(with_endpoint=True)

    def _delete(self, id, access_token="", **kwargs):
        response = super()._delete(f"/drivers/{id}", access_token)

        return response

    def test_success(self):
        driver_count = AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DRIVER_COUNT)

        response = self._delete(self.driver.user.id, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(AllTimeStat.get(Constants.ALL_TIME_STAT_TYPE_DRIVER_COUNT), driver_count - 1)

    #todo implement later
    # def test_failure_with_driver_with_ongoing_order(self):

    def test_failure_with_wrong_id(self):
        response = self._delete(999, self.admin_access_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.json["detail"], 'An object with this id does not exist')

    def test_failure_with_customer(self):
        self.permission_denied_test(self._delete(999, Manager.get_customer_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._delete(999, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized_account(self):
        self.unauthorized_account_test(self._delete(999, ""))
