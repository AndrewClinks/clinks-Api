from rest_framework.test import APIClient

from ..utils import Data

from ...user.models import User
from ...admin.models import Admin
from ...customer.models import Customer
from ...setting.models import Setting
from ...image.models import Image
from ...driver.models import Driver
from ...identification.models import Identification
from ...company_member.models import CompanyMember
from ...company.models import Company
from ...venue.models import Venue
from ...staff.models import Staff
from ...category.models import Category
from ...item.models import Item
from ...currency.models import Currency
from ...menu.models import Menu
from ...menu_category.models import MenuCategory
from ...menu_item.models import MenuItem
from ...card.models import Card
from ...availability.models import Availability
from ...order.models import Order
from ...delivery_distance.models import DeliveryDistance
from ...delivery_request.models import DeliveryRequest

from django.contrib.auth.hashers import make_password

from ...utils import Constants, Token, DateUtils

import json

client = APIClient()


def setup_db():
    if Setting.objects.first() is None:
        create_default_settings()

    if Currency.objects.first() is None:
        create_currency()

    if Availability.objects.first() is None:
        create_default_availabilities()


def create_default_settings():
    Setting.objects.create(key=Constants.SETTING_KEY_MINIMUM_AGE, value="18")
    Setting.objects.create(key=Constants.SETTING_KEY_MINIMUM_ORDER_AMOUNT, value="500")


def create_currency(name="EURO", symbol="€", iso_code="4317", code="eur"):

    currency, created = Currency.objects.get_or_create(
        name=name,
        symbol=symbol,
        iso_code=iso_code,
        code=code
    )

    return currency


def create_default_availabilities():
    time_10_30 = str(DateUtils.to_timedelta(hours=10, minutes=30))
    time_12_30 = str(DateUtils.to_timedelta(hours=12, minutes=30))
    time_21_30 = str(DateUtils.to_timedelta(hours=21, minutes=30))

    Availability.objects.create(day=Constants.DAY_MONDAY, starts_at=time_10_30, ends_at=time_21_30)
    Availability.objects.create(day=Constants.DAY_TUESDAY, starts_at=time_10_30, ends_at=time_21_30)
    Availability.objects.create(day=Constants.DAY_WEDNESDAY, starts_at=time_10_30, ends_at=time_21_30)
    Availability.objects.create(day=Constants.DAY_THURSDAY, starts_at=time_10_30, ends_at=time_21_30)
    Availability.objects.create(day=Constants.DAY_FRIDAY, starts_at=time_10_30, ends_at=time_21_30)
    Availability.objects.create(day=Constants.DAY_SATURDAY, starts_at=time_10_30, ends_at=time_21_30)
    Availability.objects.create(day=Constants.DAY_SUNDAY, starts_at=time_12_30, ends_at=time_21_30)

    Availability.objects.create(date=DateUtils.create_date(17, 3, 2020), starts_at=time_12_30, ends_at=time_21_30)
    Availability.objects.create(date=DateUtils.create_date(25, 12, 2020), closed=True)


def get_currency_euro():
    return Currency.objects.filter(name="EURO").first()


def get_access_token(user):
    return "Bearer "+Token.create(user)["access"]


def get_refresh_token(user):
    return Token.create(user)["refresh"]


def get_admin_access_token(data=None, is_super_admin=True):
    admin = create_admin(data, is_super_admin)
    return get_access_token(admin.user)


def get_admin_staff_access_token(data=None):
    return get_admin_access_token(data, False)


def get_customer_access_token(data=None):
    customer = create_customer(data)
    return get_access_token(customer.user)


def get_driver_access_token(data=None):
    driver = create_driver(data)
    return get_access_token(driver.user)


def get_company_member_access_token(data=None, company=None):
    company_member = create_company_member(data, company)
    return get_access_token(company_member.user)


def get_staff_access_token(venue=None, company=None):
    if not venue:
        venue = create_venue(company)

    staff = create_staff(venue=venue)

    return get_access_token(staff.company_member.user)


def _post(endpoint, data={}, access_token=""):
    from ...tests.TestCase import TestCase
    response = TestCase._post(endpoint, data, access_token)
    return response


def _get(endpoint, access_token=""):
    from ...tests.TestCase import TestCase
    response = TestCase._get(endpoint, access_token=access_token)
    return response

def _patch(endpoint, data={}, access_token=""):
    from ...tests.TestCase import TestCase
    response = TestCase._patch(endpoint, data, access_token)
    return response


def login(email, password):

    data = {
        "email": email,
        "password": password
    }

    response = _post("/user/login", data)
    return response


def request_reset_password(email):
    data = {"email": email}
    response = _post("/user/request-reset-password", data)
    return response


def reset_password(email, verification_code, password):
    data = {
        "email": email,
        "verification_code": verification_code,
        "password": password
    }

    response = _post("/user/reset-password", data)

    return response


def request_verify_email(access_token):
    response = _post("/user/request-verify-email", access_token=access_token)
    return response


def verify_email(access_token, code):
    data = {
        "verification_code": code
    }

    response = _post("/user/verify-email", data, access_token)

    return response


def logout(user, access_token=None, refresh_token=None):
    if not access_token:
        tokens = Token.create(user)
        access_token = "Bearer "+tokens["access"]
        refresh_token = tokens["refresh"]

    data = {
        "refresh": refresh_token
    }

    response = _post("/user/logout", data, access_token)

    return response


def user_info(access_token):
    response = _get("/user/info", access_token)
    return response


def create_admin(data=None, is_super_admin=True):
    if not data:
        data = Data.valid_admin_data()

    if is_super_admin:
        data["role"] = Constants.ADMIN_ROLE_ADMIN

    data["user"]["password"] = make_password(data["user"]["password"])
    data["user"]["role"] = Constants.USER_ROLE_ADMIN

    user = User.objects.create(**data["user"])

    data["user"] = user

    teacher = Admin.objects.create(**data)

    return teacher


def create_customer(data=None, with_identification=False):
    if not data:
        data = Data.valid_customer_data()

    if with_identification:
        identification = create_identification()
        data["identification"] = identification

    data["user"]["password"] = make_password(data["user"]["password"])
    data["user"]["role"] = Constants.USER_ROLE_CUSTOMER

    user = User.objects.create(**data["user"])

    data["user"] = user

    customer = Customer.objects.create(**data)

    return customer


def create_driver(data=None, with_endpoint=False):
    if not data:
        data = Data.valid_driver_data()

    if with_endpoint:
        response = _post("/drivers", data, get_admin_access_token())

        return Driver.objects.get(user_id=response.json["user"]["id"])

    data["user"]["password"] = make_password(data["user"]["password"])
    data["user"]["role"] = Constants.USER_ROLE_DRIVER

    user = User.objects.create(**data["user"])

    data["user"] = user

    identification_data = data.pop("identification", None)

    if identification_data:
        identification = create_identification(identification_data)
        data["identification"] = identification

    driver = Driver.objects.create(**data)

    return driver


def create_company_member(data=None, company=None):
    if not data:
        data = Data.valid_company_member_data()

    if not company:
        company = create_company()

    if company:
        data["company"] = company

    data["user"]["password"] = make_password(data["user"]["password"])
    data["user"]["role"] = Constants.USER_ROLE_COMPANY_MEMBER

    user = User.objects.create(**data["user"])

    data["user"] = user

    company_member = CompanyMember.objects.create(**data)

    return company_member


def create_image(access_token=None, mock=True):
    if not access_token:
        access_token = get_customer_access_token()

    if not mock:
        file = open("api/tests/utils/files/identification.jpeg", 'rb')

        data = {
            "file": file
        }

        header = {"content_type": "application/x-www-form-urlencoded"}

        response = client.post('/images',
                               data,
                               HTTP_AUTHORIZATION=access_token,
                               header=header)

        response_json = json.loads(response.content)

        return Image.objects.get(id=response_json["id"])

    image = Image.objects.create(original="mock-image-url.ie")

    return image


def create_identification(data=None):
    if not data:
        data = Data.valid_identification_data()

    data["front"] = Image.objects.get(id=data["front"])
    data["back"] = Image.objects.get(id=data["back"])

    identification = Identification.objects.create(**data)

    return identification


def create_company(data=None):
    if not data:
        data = Data.valid_company_data()

    response = _post("/companies", data, get_admin_access_token())

    company_id = response.json["id"]

    return Company.objects.get(id=company_id)


def create_delivery_distances(data=Data.valid_delivery_distances_data()):
    response = _post("/delivery-distances", data, get_admin_access_token())

    return response.json["delivery_distances"]


def create_venue(company=None, data=None, setup_stripe_account=True):
    from ..utils import Stripe

    if not data:
        data = Data.valid_venue_data(company)

    response = _post("/venues", data, get_admin_access_token())

    venue_id = response.json["id"]

    venue = Venue.objects.get(id=venue_id)

    if setup_stripe_account:
        Stripe.payments_enabled_account(venue.company)

    return venue


def create_staff(company_member=None, venue=None):
    data = Data.valid_staff_data(company_member, venue)

    response = _post("/staff", data, get_admin_access_token())

    staff_id = response.json["id"]

    return Staff.objects.get(id=staff_id)


def create_category(data=None):
    if not data:
        data = Data.valid_category_data()

    response = _post("/categories", data, get_admin_access_token())

    category_id = response.json["id"]

    return Category.objects.get(id=category_id)


def create_subcategory(data=None, parent=None):
    if not parent:
        parent = create_category()

    if not data:
        data = Data.valid_category_data(parent)

    return create_category(data)


def create_item(data=None, subcategory=None):
    if not data:
        data = Data.valid_item_data(subcategory=subcategory)

    response = _post("/items", data, get_admin_access_token())

    item_id = response.json["id"]

    return Item.objects.get(id=item_id)


def setup_menu(venue=None, with_menu_item=True):
    if not venue:
        venue = create_venue()

    menu_category = create_menu_category(menu=venue.menu)

    if with_menu_item:
        create_menu_item(menu=venue.menu, menu_category=menu_category)

    return Menu.objects.get(venue_id=venue.id)


def create_menu_category(data=None, menu=None, category=None):
    if not menu:
        menu = create_venue().menu

    if not data:
        data = Data.valid_menu_category_data(menu, category)

    response = _post("/menu-categories", data, get_admin_access_token())

    menu_category_id = response.json["id"]

    return MenuCategory.objects.get(id=menu_category_id)


def create_menu_item(data=None, menu=None,  menu_category=None, item=None):
    if not data and not menu:
        menu = create_venue().menu

    if not data and not menu_category:
        category = item.subcategory.parent if item else None
        menu_category = create_menu_category(menu=menu, category=category)

    if not data:
        data = Data.valid_menu_item_data(menu, menu_category, item)

    response = _post("/menu-items", data, get_admin_access_token())

    menu_item_id = response.json["id"]

    return MenuItem.objects.get(id=menu_item_id)


def create_card(customer_access_token=None, data=None):
    if not customer_access_token:
        customer_access_token = get_customer_access_token()

    if not data:
        data = Data.valid_card_data()

    response = _post("/cards", data, customer_access_token)

    card_id = response.json["id"]

    return Card.objects.get(id=card_id)


def get_action_required_card(student_access_token):
    data = Data.action_required_card_data()

    card = create_card(student_access_token, data)

    return card


def get_declined_card(student_access_token):
    data = Data.declined_card_data()

    card = create_card(student_access_token, data)

    return card


def add_address_to_customer(customer=None, address=None):
    if not customer:
        customer = create_customer()

    access_token = get_access_token(customer.user)

    if not address:
        address = Data.valid_address_data()

    data = {
        "address": address
    }

    response = _patch(f"/customers/{customer.user_id}", data, access_token)

    customer.refresh_from_db()

    return customer


def update_customer(customer=None, add_address=True, add_identification=False, use_mock_image_for_identification=True):
    if not customer:
        customer = create_customer()

    access_token = get_access_token(customer.user)

    data = {}

    if add_address:
        data.update({
            "address": Data.valid_address_data()
        })

    if add_identification:
        data.update({
            "identification": Data.valid_identification_data(use_mock_image=use_mock_image_for_identification)
        })

    response = _patch(f"/customers/{customer.user_id}", data, access_token)

    customer.refresh_from_db()

    return customer


def get_delivery_distance_for(distance):
    from ...delivery_distance.models import DeliveryDistance
    return DeliveryDistance.get_by_distance(distance)


def create_order(customer=None, data=None, company=None, venue=None, time_to_freeze="2022-01-01 12:31:01"):
    from freezegun import freeze_time

    if not customer:
        customer = create_customer()

    if not DeliveryDistance.objects.first():
        create_delivery_distances()

    if not data:
        data = Data.valid_order_data(customer, company=company, venue=venue)

    with freeze_time(time_to_freeze):
        response = _post("/orders", data, get_access_token(customer.user))

    return Order.objects.get(id=response.json["id"])


def _change_order_status(status=None, delivery_status=None, order=None, venue=None, with_company_member=True):
    if not order:
        order = create_order(venue=venue)

    if status:
        data = {
            "status": status
        }
    else:
        data = {
          "delivery_status": delivery_status
        }

    access_token = None

    if with_company_member:
        access_token = get_staff_access_token(venue=order.venue)
    else:
        order.driver = create_driver()
        order.save()
        access_token = get_access_token(order.driver.user)

    response = _patch(f"/orders/{order.id}", data, access_token)

    return Order.objects.get(id=response.json["id"])


def create_looking_for_driver_order(order=None, venue=None):
    return _change_order_status(Constants.ORDER_STATUS_LOOKING_FOR_DRIVER, order=order, venue=venue)


def get_driver_close_to_venue(driver=None, venue=None, distance_to_venue=0):
    from ..utils import Point
    if not driver:
        driver = create_driver()

    if not venue:
        venue = create_venue(data=Data.valid_venue_data(opens_everyday=True))

    venue_point = venue.address.point

    driver.last_known_location = Point.north_for_point(venue_point, distance_to_venue, True)
    driver.save()

    return driver


def get_order_looking_for_driver_with_close_driver(driver=None, venue=None, return_driver_with_order=False):
    if not venue:
        venue = create_venue(data=Data.valid_venue_data(opens_everyday=True))

    driver = get_driver_close_to_venue(driver, venue)

    order = create_looking_for_driver_order(venue=venue)

    if return_driver_with_order:
        return {"order": order, "driver": driver}

    return order


def get_delivery_request(driver=None, venue=None, order=None):
    if not order or not driver:
        response = get_order_looking_for_driver_with_close_driver(driver, venue, True)
        order = response["order"]
        driver = response["driver"]

    delivery_request = DeliveryRequest.objects.filter(order=order, driver=driver).first()

    return delivery_request


def assign_a_driver_to_order(driver=None, venue=None, delivery_request=None):
    if not driver:
        driver = create_driver()

    if not delivery_request:
        delivery_request = get_delivery_request(driver, venue)

    data = {
        "status": Constants.DELIVERY_REQUEST_STATUS_ACCEPTED
    }

    driver_access_token = get_access_token(driver.user)

    response = _patch(f"/delivery-requests/{delivery_request.id}", data, driver_access_token)

    delivery_request.refresh_from_db()

    return delivery_request


def create_rejected_order():
    order = create_order()

    staff_access_token = get_staff_access_token(venue=order.venue)

    data = {
        "status": Constants.ORDER_STATUS_REJECTED
    }

    response = _patch(f"/orders/{order.id}", data, staff_access_token)

    order.refresh_from_db()

    return order


def create_out_for_delivery_order(driver=None):
    delivery_request = assign_a_driver_to_order(driver)

    order = delivery_request.order

    staff_access_token = get_staff_access_token(venue=order.venue)

    data = {
        "delivery_status": Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY
    }

    response = _patch(f"/orders/{order.id}", data, staff_access_token)

    order.refresh_from_db()

    return order


def create_returned_order():
    order = create_out_for_delivery_order()
    driver_access_token = get_access_token(order.driver.user)
    staff_access_token = get_staff_access_token(venue=order.venue)

    data = {
        "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_REFUSED,
        "delivery_status": Constants.DELIVERY_STATUS_FAILED
    }

    response = _patch(f"/orders/{order.id}", data, driver_access_token)

    data = {
        "delivery_status": Constants.DELIVERY_STATUS_RETURNED
    }

    response = _patch(f"/orders/{order.id}", data, staff_access_token)

    order.refresh_from_db()

    return order


def create_delivered_order(driver=None):
    order = create_out_for_delivery_order(driver)
    driver_access_token = get_access_token(order.driver.user)

    data = {
        "delivery_status": Constants.DELIVERY_STATUS_DELIVERED,
        "identification_status": Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUESTED
    }

    response = _patch(f"/orders/{order.id}", data, driver_access_token)

    order.refresh_from_db()

    return order


def reject_a_delivery_request(delivery_request):
    driver = delivery_request.driver
    driver_access_token = get_access_token(driver.user)

    data = {
        "status": Constants.DELIVERY_REQUEST_STATUS_REJECTED
    }

    response = _patch(f"/delivery-requests/{delivery_request.id}", data, driver_access_token)

    delivery_request.refresh_from_db()

    return delivery_request


def accept_a_delivery_request(delivery_request):
    driver = delivery_request.driver
    driver_access_token = get_access_token(driver.user)

    data = {
        "status": Constants.DELIVERY_REQUEST_STATUS_ACCEPTED
    }

    response = _patch(f"/delivery-requests/{delivery_request.id}", data, driver_access_token)

    print(response.json)

    delivery_request.refresh_from_db()

    return delivery_request

