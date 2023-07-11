from rest_framework.test import APIClient
from rest_framework import status

from ...venue.models import Venue
from ...menu_item.models import MenuItem
from ...item.models import Item
from ...category.models import Category
from ...payment.models import Payment
from ...all_time_stat.models import AllTimeStat
from ...daily_stat.models import DailyStat
from ...availability.models import Availability
from ...setting.models import Setting
from ...delivery_distance.models import DeliveryDistance
from ...driver_payment.models import DriverPayment

from ...company.models import Company
from ...tests.TestCase import TestCase

from ..utils import Data, Manager, Point

from freezegun import freeze_time

import os
from ...utils import Constants, List, DateUtils


class CreateTest(TestCase):

    client = APIClient()

    def setUp(self):
        self.customer = Manager.create_customer()

        self.customer_access_token = Manager.get_access_token(self.customer.user)

        self.venue = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))

        self.menu = self.venue.menu

        Manager.create_delivery_distances()

    def _post(self, data, access_token="", **kwargs):
        response = super()._post("/orders", data, access_token)

        return response

    def test_success(self):
        venue = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))
        Manager.setup_menu(venue)

        today = DateUtils.today().date()

        post_data = Data.valid_order_data(self.customer)

        snapshot = self.take_snapshot(post_data)

        response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json["venue"]["id"], post_data["venue"])

        data = response.json["data"]
        self.assertTrue("customer_address" in data)
        self.assertEqual(data["customer_address"]["id"], post_data["address"])

        self.assertTrue("venue_address" in data)
        self.assertEqual(data["venue_address"]["id"], snapshot["venue"].address.id)

        self.assertTrue("card" in data)
        self.assertEqual(data["card"]["customer"], self.customer.user_id)

        self.items_and_stats_validation(response, post_data, snapshot, str(today))

        payment = Payment.objects.get(id=response.json["payment"]["id"])

        venue = Venue.objects.get(id=response.json["venue"]["id"])

        self.assertEqual(payment.company, venue.company)

        order = payment.order

        self.assertIsNone(order.identification_status)
        self.assertIsNone(order.rejection_reason)

        if not os.environ.get("CI", False):
            self.assertIsNotNone(order.receipt)

    def test_with_sale_items(self):
        menu_item = Manager.create_menu_item(data=Data.valid_menu_item_data(self.menu, price_sale=200))
        order_item_data = Data.valid_order_item_data(menu_item, 2)
        order_items_data = Data.valid_order_items_data(self.menu)
        order_items_data.append(order_item_data)
        post_data = Data.valid_order_data(self.customer, venue=self.venue, order_items=order_items_data)

        snapshot = self.take_snapshot(post_data)

        with freeze_time("2022-04-04 10:30:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.items_and_stats_validation(response, post_data, snapshot, "2022-04-04")

    def test_with_free_items(self):
        menu_item = Manager.create_menu_item(data=Data.valid_menu_item_data(self.menu, price_sale=200))
        menu_item.price_sale = 0
        menu_item.save()

        order_item_data = Data.valid_order_item_data(menu_item, 1)
        order_items_data = Data.valid_order_items_data(self.menu)
        order_items_data.append(order_item_data)
        post_data = Data.valid_order_data(self.customer, venue=self.venue, order_items=order_items_data)

        snapshot = self.take_snapshot(post_data)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.items_and_stats_validation(response, post_data, snapshot, "2022-01-01")

        payment = Payment.objects.get(order=response.json["id"])

        self.assertEqual(payment.amount, self.menu.items.last().price)

    def test_with_duplicated_item(self):
        order_item_data = Data.valid_order_item_data(menu=self.menu)

        order_items_data = [
            order_item_data,
            order_item_data
        ]

        post_data = Data.valid_order_data(self.customer, venue=self.venue, order_items=order_items_data)

        snapshot = self.take_snapshot(post_data)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.items_and_stats_validation(response, post_data, snapshot, "2022-01-01")

    def test_with_service_fee_less_than_50_cents(self):
        self.venue.service_fee_percentage = 0
        self.venue.save()

        post_data = Data.valid_order_data(self.customer, venue=self.venue)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(id=response.json["payment"]["id"])

        self.assertEqual(payment.service_fee, 50)

    def test_with_service_fee_more_than_2_euro(self):
        self.venue.service_fee_percentage = 0.9
        self.venue.save()

        post_data = Data.valid_order_data(self.customer, venue=self.venue, tip=200)

        subtotal = Data.calculate_payment_values_for(post_data["items"], self.venue, self.customer, 200)["subtotal"]

        service_fee = int(subtotal * self.venue.service_fee_percentage)
        self.assertGreater(service_fee, 200)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(id=response.json["payment"]["id"])

        self.assertEqual(payment.service_fee, 200)

    def test_with_service_fee_between_50_cents_and_2_euro(self):
        self.assertIsNotNone(self.venue.service_fee_percentage)
        self.venue.service_fee_percentage = 0.1
        self.venue.save()

        post_data = Data.valid_order_data(self.customer, venue=self.venue, tip=200)

        service_fee = Data.calculate_payment_values_for(post_data["items"], self.venue, self.customer, 200)["service_fee"]

        self.assertLess(service_fee, 200)
        self.assertGreater(service_fee, 50)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(id=response.json["payment"]["id"])

        self.assertEqual(payment.service_fee, service_fee)

    def test_with_different_delivery_fees(self):
        delivery_distance_0_to_5 = DeliveryDistance.objects.filter(starts=0, ends=5).first()
        delivery_distance_5_to_6 = DeliveryDistance.objects.create(starts=5, ends=6, fee=1200, driver_fee=1000)
        delivery_distance_6_to_10 = DeliveryDistance.objects.create(starts=6, ends=10, fee=1400, driver_fee=1200)

        venue_point = self.venue.address.point

        _5_km_away = Point.north_for_point(venue_point, 5)
        _5_km_away_address = Manager.add_address_to_customer(self.customer, Data.valid_address_data(latitude=_5_km_away.latitude, longitude=_5_km_away.longitude)).address

        post_data = Data.valid_order_data(self.customer, venue=self.venue, address=_5_km_away_address)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(id=response.json["payment"]["id"])
        self.assertEqual(payment.delivery_fee, delivery_distance_0_to_5.fee)
        self.assertEqual(payment.delivery_driver_fee, delivery_distance_0_to_5.driver_fee)

        _6_km_away = Point.north_for_point(venue_point, 6)
        _6_km_away_address = Manager.add_address_to_customer(self.customer,
                                                             Data.valid_address_data(latitude=_6_km_away.latitude,
                                                                                     longitude=_6_km_away.longitude)).address

        post_data = Data.valid_order_data(self.customer, venue=self.venue, address=_6_km_away_address)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(id=response.json["payment"]["id"])
        self.assertEqual(payment.delivery_fee, delivery_distance_5_to_6.fee)
        self.assertEqual(payment.delivery_driver_fee, delivery_distance_5_to_6.driver_fee)

        _6_1_km_away = Point.north_for_point(venue_point, 6.1)
        _6_1_km_away_address = Manager.add_address_to_customer(self.customer,
                                                             Data.valid_address_data(latitude=_6_1_km_away.latitude,
                                                                                     longitude=_6_1_km_away.longitude)).address

        post_data = Data.valid_order_data(self.customer, venue=self.venue, address=_6_1_km_away_address)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(id=response.json["payment"]["id"])
        self.assertEqual(payment.delivery_fee, delivery_distance_6_to_10.fee)
        self.assertEqual(payment.delivery_driver_fee, delivery_distance_6_to_10.driver_fee)


    def test_delivery_fees_with_different_distance(self):
        from ...utils import Distance

        delivery_distance = DeliveryDistance.objects.order_by("-ends").first()
        previous_delivery_distance_ends = delivery_distance.ends
        delivery_distance.ends = 2000
        delivery_distance.save()

        venue = Manager.create_venue()
        Manager.setup_menu(venue)
        venue.address.point = Point.from_lat_and_lng_to_db(53.279429, -6.4455236)
        venue.address.save()
        venue_point = venue.address.point

        latitude = 53.2135349
        longitude = -6.243300800000001
        customer_point = Point.from_lat_and_lng_to_db(latitude, longitude)

        distance_1 = Distance.between(venue_point, customer_point, True)

        response = super()._get(
            f"/menu-items?venue_id={venue.id}&latitude={latitude}&longitude={longitude}")

        self.assertEqual(int(response.json["results"][0]["venue"]["distance"]/1000), int(distance_1))

        latitude = 53.1135349
        longitude = -6.243300800000001
        customer_point = Point.from_lat_and_lng_to_db(latitude, longitude)

        distance_1 = Distance.between(venue_point, customer_point, True)

        response = super()._get(
            f"/menu-items?venue_id={venue.id}&latitude={latitude}&longitude={longitude}")

        self.assertEqual(int(response.json["results"][0]["venue"]["distance"] / 1000), int(distance_1))

        latitude = 53.2635349
        longitude = -6.343300800000001
        customer_point = Point.from_lat_and_lng_to_db(latitude, longitude)

        distance_1 = Distance.between(venue_point, customer_point, True)

        response = super()._get(
            f"/menu-items?venue_id={venue.id}&latitude={latitude}&longitude={longitude}")

        self.assertEqual(int(response.json["results"][0]["venue"]["distance"] / 1000), int(distance_1))

        latitude = 53.2635349
        longitude = -6.443300800000001
        customer_point = Point.from_lat_and_lng_to_db(latitude, longitude)

        distance_1 = Distance.between(venue_point, customer_point, True)

        response = super()._get(
            f"/menu-items?venue_id={venue.id}&latitude={latitude}&longitude={longitude}")

        self.assertEqual(int(response.json["results"][0]["venue"]["distance"] / 1000), int(distance_1))

        latitude = 53.2735349
        longitude = -6.445300800000001
        customer_point = Point.from_lat_and_lng_to_db(latitude, longitude)

        distance_1 = Distance.between(venue_point, customer_point, True)

        response = super()._get(
            f"/menu-items?venue_id={venue.id}&latitude={latitude}&longitude={longitude}")

        self.assertEqual(int(response.json["results"][0]["venue"]["distance"] / 1000), int(distance_1))

        # restore back
        delivery_distance.ends = previous_delivery_distance_ends
        delivery_distance.save()


    def test_failure_with_invalid_quantity(self):
        post_data = Data.valid_order_data()
        post_data["items"][0]["quantity"] = None

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["items"][0]["quantity"][0], 'This field may not be null.')

        post_data["items"][0]["quantity"] = 0

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["items"][0]["quantity"][0], 'Ensure this value is greater than or equal to 1.')

    def test_failure_with_out_of_delivery_zone(self):
        max_delivery_distance = DeliveryDistance.objects.order_by("-ends").first().ends
        venue_point = self.venue.address.point

        point = Point.north_for_point(venue_point, round(max_delivery_distance+1))
        address = Manager.add_address_to_customer(self.customer, Data.valid_address_data(latitude=point.latitude, longitude=point.longitude)).address

        post_data = Data.valid_order_data(self.customer, venue=self.venue, address=address, include_delivery_fee=False)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Venue does not deliver to your location')

    def test_failure_with_menu_item_does_not_exist(self):
        post_data = Data.valid_order_data(self.customer)
        post_data["items"][0]["id"] = 9999

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["items"][0]["non_field_errors"][0], 'Menu item does not exist')

    def test_failure_with_menu_item_belongs_to_different_venue_from_same_company(self):
        venue_2 = Manager.create_venue(data=Data.valid_venue_data(company=self.venue.company, opens_everyday=True))

        data = Data.valid_order_data(self.customer, venue=self.venue)

        data["venue"] = venue_2.id

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'This menu does not belong to this venue')

    def test_failure_with_subtotal_less_than_minimum_order_amount(self):
        minimum_order_amount = Setting.get_minimum_order_amount()
        menu_item = Manager.create_menu_item(data=Data.valid_menu_item_data(self.menu, price=minimum_order_amount-2))
        order_item_data = Data.valid_order_item_data(menu_item)

        post_data = Data.valid_order_data(self.customer, venue=self.venue, order_items=[order_item_data])

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Minimum order value has not reached')

    def test_failure_with_negative_tip(self):
        data = Data.valid_order_data(self.customer, tip=-1)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["payment"]["tip"][0], 'Ensure this value is greater than or equal to 0.')

    def test_failure_with_menu_item_belongs_to_different_company(self):
        order_items = Data.valid_order_items_data(self.venue.menu)

        company = Manager.create_company()
        company.status = Constants.COMPANY_STATUS_ACTIVE
        company.save()

        data = Data.valid_order_data(self.customer, company=company, order_items=order_items)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'You have menu item does not belong to current venue')

    def test_failure_with_address_belongs_to_someone_else(self):
        address = Manager.add_address_to_customer().address
        data = Data.valid_order_data(self.customer, address=address, include_delivery_fee=False)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'This address does not belong to you')

    def test_failure_with_empty_items(self):
        data = Data.valid_order_data(self.customer)
        data["items"] = []

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["items"]["non_field_errors"][0], 'This list may not be empty.')

        data["items"] = None

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["items"][0], 'This field may not be null.')

    def test_failure_with_ordering_platform_off_time_or_date(self):
        data = Data.valid_order_data(self.customer)

        with freeze_time("2021-03-17 12:29:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Whoops we are not open yet')

        with freeze_time("2021-03-17 21:31:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Sorry we are closed, come back tomorrow')

        with freeze_time("2021-12-25 12:31:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json["Order"][0], 'Sorry we are closed')

        availability = Availability.objects.get(day=Constants.DAY_FRIDAY)

        availability.closed = True
        availability.save()

        with freeze_time("2022-12-25 12:31:01"):
            response = self._post(data, Manager.get_access_token(self.customer.user))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json["Order"][0], 'Sorry we are closed')

    def test_failure_with_venue_off_time_or_date(self):
        tomorrow = DateUtils.weekday(DateUtils.tomorrow()).lower()
        opening_hour = Data.valid_opening_hour(tomorrow)

        venue = Manager.create_venue(data=Data.valid_venue_data(opening_hours=[opening_hour]))

        data = Data.valid_order_data(self.customer, venue=venue)

        today = DateUtils.today().date()

        with freeze_time(f"{today} 12:31:01"):
            response = self._post(data, Manager.get_access_token(self.customer.user))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Venue is closed')

        today = DateUtils.weekday().lower()

        opening_hour = venue.opening_hours.first()
        opening_hour.day = today
        opening_hour.starts_at = DateUtils.minutes_later(2)
        opening_hour.ends_at = DateUtils.minutes_later(12)
        opening_hour.save()

        data = Data.valid_order_data(self.customer, venue=venue)

        with freeze_time(f"{today} 12:31:01"):
            response = self._post(data, Manager.get_access_token(self.customer.user))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Venue is closed')

    def test_failure_with_company_with_uncompleted_stripe_account(self):
        venue = Manager.create_venue(data=Data.valid_venue_data(opens_everyday=True))
        company = venue.company

        data = Data.valid_order_data(self.customer, venue=venue)
        company.status = Constants.COMPANY_STATUS_ACTIVE
        company.stripe_account_id = None
        company.stripe_verification_status = Constants.STRIPE_VERIFICATION_STATUS_UNVERIFIED
        company.save()

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json["Order"][0], 'This company cannot accept payments yet!')

    def test_failure_with_not_matching_expected_price(self):
        data = Data.valid_order_data(self.customer)
        data["payment"]["expected_price"] = 100

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Payment"][0], 'The price of items on your basket has changed, please recreate your order')

    def test_failure_with_invalid_ids(self):
        data = {
            "venue": 99999,
            "menu": 99999,
            "address": 99999,
            "payment": {
                "card": 99999,
                "expected_price": 99999,
                "tip": 99999
            },
            "items": [
                {
                    "id": 99999,
                    "quantity": 1
                }
            ]
        }

        response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["venue"][0], 'Invalid pk "99999" - object does not exist.')
        self.assertEqual(response.json["address"][0], 'Invalid pk "99999" - object does not exist.')
        self.assertEqual(response.json["menu"][0], 'Invalid pk "99999" - object does not exist.')
        self.assertEqual(response.json["items"][0]["non_field_errors"][0], 'Menu item does not exist')

        data = Data.valid_order_data(self.customer)
        data["items"].append({"id": "9999", "quantity": 1})

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = Data.valid_order_data(self.customer)
        data["payment"]["card"] = 99999

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["card"][0], 'Invalid pk "99999" - object does not exist.')

    def test_failure_with_bad_card(self):
        card = Manager.create_card(self.customer_access_token, Data.declined_card_data())
        data = Data.valid_order_data(self.customer, card=card)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue("Your card was declined." in response.json["Payment"][0])

        card = Manager.create_card(self.customer_access_token, Data.action_required_card_data())
        data = Data.valid_order_data(self.customer, card=card)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["payment_intent_id"])
        self.assertIsNotNone(response.json["client_secret"])
        self.assertTrue(response.json["requires_action"])

        card = Manager.create_card(self.customer_access_token, Data.insufficent_funds_card_data())
        data = Data.valid_order_data(self.customer, card=card)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.json["payment_intent_id"])
        self.assertIsNotNone(response.json["client_secret"])
        self.assertTrue(response.json["requires_action"])

    def test_failure_with_missing_data(self):
        data = {}

        response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["venue"][0], 'This field is required.')
        self.assertEqual(response.json["address"][0], 'This field is required.')
        self.assertEqual(response.json["menu"][0], 'This field is required.')
        self.assertEqual(response.json["payment"][0], 'This field is required.')
        self.assertEqual(response.json["payment"][0], 'This field is required.')

        data = Data.valid_order_data()
        data["payment"] = {}
        data["items"] = [{}]

        response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["payment"]["card"][0], 'This field is required.')
        self.assertEqual(response.json["payment"]["expected_price"][0], 'This field is required.')
        self.assertEqual(response.json["items"][0]["id"][0], 'This field is required.')
        self.assertEqual(response.json["items"][0]["quantity"][0], 'This field is required.')

    def test_failure_with_card_belongs_to_someone_else(self):
        card = Manager.create_card()

        data = Data.valid_order_data(self.customer, card=card)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Payment"][0], 'This card with this id does not exist')

    def test_with_account_belongs_to_someone_else(self):
        data = Data.valid_order_data(self.customer)

        response = self._post(data, Manager.get_customer_access_token())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_failure_with_paused_company(self):
        from ..utils import Stripe
        company = Manager.create_company()
        Stripe.payments_enabled_account(company)
        venue = Manager.create_venue(company=company, data=Data.valid_venue_data(company, opens_everyday=True))

        company.status = Constants.COMPANY_STATUS_PAUSED
        company.save()

        post_data = Data.valid_order_data(self.customer, venue=venue)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json["Order"][0], "Sorry, this company isn't active!")

    def test_with_timezones(self):
        post_data = Data.valid_order_data(self.customer)

        venue = Venue.objects.get(id=post_data["venue"])
        venue.opening_hours.update(starts_at="11:00", ends_at="20:30")

        with freeze_time("2022-01-01 10:30:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Venue is closed')

        with freeze_time("2022-04-04 10:30:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with freeze_time("2022-01-01 11:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with freeze_time("2022-04-04 11:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with freeze_time("2022-01-01 20:31:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Venue is closed')

        with freeze_time("2022-04-04 20:31:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Sorry we are closed, come back tomorrow')

        with freeze_time("2022-01-01 20:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with freeze_time("2022-04-04 20:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Venue is closed')

        with freeze_time("2022-04-04 19:30:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Venue is closed')

        with freeze_time("2022-04-04 19:29:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_with_different_prices_delivery_fee(self):
        post_data = Data.valid_order_data(self.customer, venue=self.venue)

        items = post_data["items"]

        menu_item = MenuItem.objects.get(id=items[0]["id"])
        menu_item.price = 0
        menu_item.save()

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], 'Minimum order value has not reached')

        Setting.update(Constants.SETTING_KEY_MINIMUM_ORDER_AMOUNT, 0)

        post_data = Data.valid_order_data(self.customer, venue=self.venue, order_items=items)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.filter(order=response.json["id"]).first()

        self.assertEqual(payment.amount, 0)
        self.assertEqual(payment.delivery_fee, 1000)
        self.assertEqual(payment.service_fee, 50)
        self.assertEqual(payment.total, 1050)

        DeliveryDistance.objects.update(fee=0)

        post_data = Data.valid_order_data(self.customer, venue=self.venue, order_items=items)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.filter(order=response.json["id"]).first()

        self.assertEqual(payment.amount, 0)
        self.assertEqual(payment.delivery_fee, 0)
        self.assertEqual(payment.service_fee, 50)
        self.assertEqual(payment.total, 50)

        menu_item.price = 150
        menu_item.save()

        post_data = Data.valid_order_data(self.customer, venue=self.venue, order_items=items)

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_failure_with_paused_venue(self):
        post_data = Data.valid_order_data(self.customer, venue=self.venue)

        self.venue.paused = True
        self.venue.save()

        with freeze_time("2022-01-01 12:00:01"):
            response = self._post(post_data, self.customer_access_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json["Order"][0], "Sorry, this venue isn't active!")

    def test_failure_with_admin(self):
        self.permission_denied_test(self._post({}, Manager.get_admin_access_token()))

    def test_failure_with_company_member(self):
        self.permission_denied_test(self._post({}, Manager.get_company_member_access_token()))

    def test_failure_with_driver(self):
        self.permission_denied_test(self._post({}, Manager.get_driver_access_token()))

    def test_failure_with_unauthorized(self):
        self.unauthorized_account_test(self._post({}))

    def take_snapshot(self, post_data):

        venue_before = Venue.objects.get(id=post_data["venue"])
        company_before = venue_before.company
        customer_before = self.customer
        all_time_stats_before = list(AllTimeStat.objects.all())
        daily_stats_before = list(DailyStat.objects.all())

        return {
            "venue": venue_before,
            "company": company_before,
            "customer": customer_before,
            "all_time_stats": all_time_stats_before,
            "daily_stats": daily_stats_before
        }

    def items_and_stats_validation(self, response, post_data, snapshot, date_str):
        data = response.json["data"]
        self.data_items_validation(data, post_data)
        self.check_stats(response, post_data, snapshot, date_str)

    def data_items_validation(self, data, post_data):
        self.assertTrue("items" in data)
        menu_items = data["items"]
        post_data_items = post_data["items"]

        self.assertEqual(len(menu_items), len(post_data_items))

        for index, item in enumerate(post_data_items):
            self.assertEqual(menu_items[index]["id"], item["id"])
            self.assertEqual(menu_items[index]["quantity"], item["quantity"])

        items = []
        subcategories = []
        categories = []

        for menu_item in menu_items:
            item = menu_item["item"]
            subcategory = item["subcategory"]
            category = subcategory["parent"]

            items.append(item)
            subcategories.append(subcategory)
            categories.append(category)

        menu_item_with_occurrences = List.count_occurrence(menu_items, "id")
        items_with_occurrences = List.count_occurrence(items, "id")
        subcategories_with_occurrences = List.count_occurrence(subcategories, "id")
        categories_with_occurrences = List.count_occurrence(categories, "id")

        for data in menu_item_with_occurrences:
            menu_item = MenuItem.objects.get(id=data["item"]["id"])
            self.assertEqual(menu_item.sales_count, data["occurrence"])

        for data in items_with_occurrences:
            item = Item.objects.get(id=data["item"]["id"])
            self.assertEqual(item.sales_count, data["occurrence"])

        for data in subcategories_with_occurrences:
            item = Category.objects.get(id=data["item"]["id"])
            self.assertEqual(item.sales_count, data["occurrence"])

        for data in categories_with_occurrences:
            item = Category.objects.get(id=data["item"]["id"])
            self.assertEqual(item.sales_count, data["occurrence"])

    def check_stats(self, response, post_data, snapshot, date_str):
        venue = snapshot["venue"]
        customer = snapshot["customer"]
        company = snapshot["company"]
        all_time_stats = snapshot["all_time_stats"]
        daily_stats = snapshot["daily_stats"]

        payment = Payment.objects.get(id=response.json["payment"]["id"])

        payment_values = Data.calculate_payment_values_for(post_data["items"], venue, customer,
                                                           payment.tip)
        expected_price = payment_values["expected_price"]
        delivery_fee = payment_values["delivery_fee"]
        service_fee = payment_values["service_fee"]
        tip = post_data["payment"]["tip"]
        amount = expected_price - delivery_fee - service_fee - tip
        driver_earning = payment_values["driver_fee"] + tip
        platform_fee = service_fee

        self.assertEqual(payment.total, expected_price)
        self.assertEqual(payment.tip, tip)
        self.assertEqual(payment.card.customer.user_id, self.customer.user_id)

        self.assertEqual(payment.service_fee, service_fee)
        self.assertEqual(payment.amount, amount)
        self.assertIsNotNone(payment.stripe_fee)
        self.assertIsNotNone(payment.stripe_charge_id)

        venue_sales_count = venue.sales_count
        venue_total_earnings = venue.total_earnings

        company_sales_count = company.sales_count
        company_total_earnings = company.total_earnings

        customer_last_order_at = customer.last_order_at
        customer_order_count = customer.order_count
        customer_total_spending = customer.total_spending
        customer_average_spending_per_order = customer.average_spending_per_order

        venue.refresh_from_db()
        company.refresh_from_db()
        customer.refresh_from_db()

        self.assertEqual(venue.sales_count, venue_sales_count + 1)
        self.assertEqual(venue.total_earnings, venue_total_earnings + amount)

        self.assertEqual(company.sales_count, company_sales_count + 1)
        self.assertEqual(company.total_earnings, company_total_earnings + amount)

        self.assertNotEqual(customer_last_order_at, customer.last_order_at)
        self.assertEqual(customer.order_count, customer_order_count + 1)
        self.assertEqual(customer.total_spending, customer_total_spending + expected_price)
        self.assertNotEqual(customer.average_spending_per_order, customer_average_spending_per_order)
        self.assertEqual(customer.average_spending_per_order, customer.total_spending / customer.order_count)

        all_time_total_earnings_before = self._get_all_time_stats_for_type(Constants.ALL_TIME_STAT_TYPE_TOTAL_EARNINGS,
                                                                           all_time_stats)
        all_time_total_earnings_after = self._get_all_time_stats_for_type(Constants.ALL_TIME_STAT_TYPE_TOTAL_EARNINGS)
        all_time_company_earnings_before = self._get_all_time_stats_for_type(
            Constants.ALL_TIME_STAT_TYPE_TOTAL_COMPANY_EARNINGS, all_time_stats)
        all_time_company_earnings_after = self._get_all_time_stats_for_type(
            Constants.ALL_TIME_STAT_TYPE_TOTAL_COMPANY_EARNINGS)
        all_time_driver_earnings_before = self._get_all_time_stats_for_type(
            Constants.ALL_TIME_STAT_TYPE_TOTAL_DRIVER_EARNINGS, all_time_stats)
        all_time_driver_earnings_after = self._get_all_time_stats_for_type(
            Constants.ALL_TIME_STAT_TYPE_TOTAL_DRIVER_EARNINGS)
        all_time_platform_earnings_before = self._get_all_time_stats_for_type(
            Constants.ALL_TIME_STAT_TYPE_PLATFORM_EARNINGS, all_time_stats)
        all_time_platform_earnings_after = self._get_all_time_stats_for_type(
            Constants.ALL_TIME_STAT_TYPE_PLATFORM_EARNINGS)
        all_time_sales_count_before = self._get_all_time_stats_for_type(Constants.ALL_TIME_STAT_TYPE_SALES_COUNT,
                                                                        all_time_stats)
        all_time_sales_count_after = self._get_all_time_stats_for_type(Constants.ALL_TIME_STAT_TYPE_SALES_COUNT)

        self.assertEqual(all_time_total_earnings_after, all_time_total_earnings_before + payment.total)
        self.assertEqual(all_time_company_earnings_after, all_time_company_earnings_before + amount)
        self.assertEqual(all_time_driver_earnings_after, all_time_driver_earnings_before + driver_earning)
        self.assertEqual(all_time_platform_earnings_after, all_time_platform_earnings_before + platform_fee)
        self.assertEqual(all_time_sales_count_after, all_time_sales_count_before + 1)

        date = DateUtils.parse(date_str).date()
        daily_stats_total_earnings_before = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_TOTAL_EARNINGS, date,
                                                                      daily_stats_before=daily_stats)
        daily_stats_total_earnings_after = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_TOTAL_EARNINGS, date)
        daily_stats_total_company_earnings_before = self._get_daily_stats_for(
            Constants.DAILY_STAT_TYPE_TOTAL_COMPANY_EARNINGS, date, daily_stats_before=daily_stats)
        daily_stats_total_company_earnings_after = self._get_daily_stats_for(
            Constants.DAILY_STAT_TYPE_TOTAL_COMPANY_EARNINGS, date)
        daily_stats_venue_earnings_before = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_TOTAL_COMPANY_EARNINGS,
                                                                      date, venue, daily_stats_before=daily_stats)
        daily_stats_venue_earnings_after = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_TOTAL_COMPANY_EARNINGS,
                                                                     date, venue)
        daily_stats_company_earnings_before = self._get_daily_stats_for(
            Constants.DAILY_STAT_TYPE_TOTAL_COMPANY_EARNINGS, date, company=company, daily_stats_before=daily_stats)
        daily_stats_company_earnings_after = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_TOTAL_COMPANY_EARNINGS,
                                                                       date, company=company)
        daily_stats_driver_earnings_before = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_TOTAL_DRIVER_EARNINGS,
                                                                       date, daily_stats_before=daily_stats)
        daily_stats_driver_earnings_after = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_TOTAL_DRIVER_EARNINGS,
                                                                      date)
        daily_stats_platform_earnings_before = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_PLATFORM_EARNINGS,
                                                                         date, daily_stats_before=daily_stats)
        daily_stats_platform_earnings_after = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_PLATFORM_EARNINGS,
                                                                        date)

        daily_stats_sales_count_before = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_SALES_COUNT, date,
                                                                   daily_stats_before=daily_stats)
        daily_stats_sales_count_after = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_SALES_COUNT, date)
        daily_stats_venue_sales_count_before = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_SALES_COUNT, date,
                                                                         venue, daily_stats_before=daily_stats)
        daily_stats_venue_sales_count_after = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_SALES_COUNT, date,
                                                                        venue)
        daily_stats_company_sales_count_before = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_SALES_COUNT, date,
                                                                           company=company,
                                                                           daily_stats_before=daily_stats)
        daily_stats_company_sales_count_after = self._get_daily_stats_for(Constants.DAILY_STAT_TYPE_SALES_COUNT, date,
                                                                          company=company)

        self.assertEqual(daily_stats_total_earnings_after, daily_stats_total_earnings_before + payment.total)
        self.assertEqual(daily_stats_total_company_earnings_after,
                         daily_stats_total_company_earnings_before + payment.amount)
        self.assertEqual(daily_stats_venue_earnings_after, daily_stats_venue_earnings_before + payment.amount)
        self.assertEqual(daily_stats_company_earnings_after, daily_stats_company_earnings_before + payment.amount)
        self.assertEqual(daily_stats_driver_earnings_after, daily_stats_driver_earnings_before + driver_earning)
        self.assertEqual(daily_stats_platform_earnings_after, daily_stats_platform_earnings_before + platform_fee)
        self.assertEqual(daily_stats_sales_count_after, daily_stats_sales_count_before + 1)
        self.assertEqual(daily_stats_venue_sales_count_after, daily_stats_venue_sales_count_before + 1)
        self.assertEqual(daily_stats_company_sales_count_after, daily_stats_company_sales_count_before + 1)

    def _get_all_time_stats_for_type(self, type, all_time_stats_before=None):
        if all_time_stats_before:
            value = getattr(List.find(all_time_stats_before, "type", type), "value", 0)
        else:
            value = AllTimeStat.objects.get(type=type).value

        return int(value)

    def _get_daily_stats_for(self, type, date, venue=None, company=None, daily_stats_before=None):
        if daily_stats_before is not None:
            found = None
            for current_object in daily_stats_before:
                if current_object.type == type and current_object.date == date and current_object.venue == venue and current_object.company == company:
                    found = current_object
                    break
            return 0 if not found else int(found.value)

        daily_stat = DailyStat.objects.filter(type=type, date=date, venue=venue, company=company).first()

        if not daily_stat:
            return 0
        value = daily_stat.value

        return int(value)