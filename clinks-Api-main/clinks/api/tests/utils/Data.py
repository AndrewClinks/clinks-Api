import uuid

import shortuuid

from ...utils import Constants, DateUtils
from ..utils import Stripe

TEST_EMAIL = "a@b.c"


def valid_admin_data(email=None, first_name="Admin Name", last_name="Surname"):
    if not email:
        email = f"admin_{shortuuid.uuid()}@clinks.ie"

    return {
        "user": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": "Aa!89032"
        }
    }


def valid_customer_data(email=None, first_name="Customer Name", last_name="Surname", date_of_birth="1990-01-01",
                        with_identification=False, with_phone_number=False):
    if not email:
        email = f"customer_{shortuuid.uuid()}@clinks.ie"

    data = {
        "user": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": "Aa!89032",
            "date_of_birth": date_of_birth
        }
    }

    if with_phone_number:
        data['user'].update({
            "phone_country_code": "+353",
            "phone_number": "123456789"
        })

    if with_identification:
        data.update({"identification": valid_identification_data(type=Constants.IDENTIFICATION_TYPE_AGE_CARD)})

    return data


def valid_driver_data(email=None, first_name="Driver Name", last_name="Surname", with_license=False):
    if not email:
        email = f"driver_{shortuuid.uuid()}@clinks.ie"

    vehicle_type = Constants.VEHICLE_TYPE_BICYCLE if not with_license else Constants.VEHICLE_TYPE_CAR
    identification = None if not with_license else valid_identification_data(
        type=Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE)
    vehicle_registration_no = None if not with_license else "vehicle_registration_no"

    return {
        "user": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": "Aa!89032",
            "phone_country_code": "+353",
            "phone_number": "123456789"
        },
        "ppsn": "ppsn",
        "vehicle_type": vehicle_type,
        "identification": identification,
        "vehicle_registration_no": vehicle_registration_no
    }


def valid_company_member_data(email=None, first_name="Company Member Name", last_name="Surname", company=None, venue=None):
    if not email:
        email = f"company_member_{shortuuid.uuid()}@clinks.ie"

    data = {
        "user": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": "Aa!89032",
            "phone_country_code": "+353",
            "phone_number": "123456789"
        },
    }

    if company:
        data.update({"company": company.id})

    if venue:
        data.update({"venue": venue.id})

    return data


def valid_identification_data(front=None, back=None, type=Constants.IDENTIFICATION_TYPE_AGE_CARD, use_mock_image=True):
    from . import Manager

    if not front:
        front = Manager.create_image(mock=use_mock_image)

    if not back:
        back = Manager.create_image(mock=use_mock_image)

    return {
        "front": front.id,
        "back": back.id,
        "type": type
    }


def valid_company_data(title="company", members=None, logo=None, featured_image=None):
    from . import Manager

    if not members:
        members = [valid_company_member_data()]

    if not logo:
        logo = Manager.create_image()

    if not featured_image:
        featured_image = Manager.create_image()

    return {
        "title": title,
        "members": members,
        "featured_image": featured_image.id,
        "logo": logo.id,
        "eircode": "eircode",
        "vat_no": "vat_no",
        "liquor_license_no": "liquor_license_no"
    }


def valid_address_data(line_1="baggot street", latitude=53.3331671, longitude=-6.243948):
    return {
        "line_1": line_1,
        "line_2": None,
        "line_3": None,
        "city": "Dublin",
        "country": "Ireland",
        "state": "Dublin",
        "latitude": latitude,
        "longitude": longitude,
        "postal_code": None,
        "country_short": "IE"
    }


def valid_delivery_distance_data(starts=0, ends=5, fee=1000, driver_fee=800):
    return {
        "starts": starts,
        "ends": ends,
        "fee": fee,
        "driver_fee": driver_fee
    }


def valid_delivery_distances_data(distances=None):
    if not distances:
        distances = [
            valid_delivery_distance_data(0, 5, 1000)
        ]

    return {
        "delivery_distances": distances
    }


def valid_delivery_distances_with(starts=0, ends=5, fee=1000, driver_fee=800):
    return {
        "delivery_distances": [
            {
                "starts": starts,
                "ends": ends,
                "fee": fee,
                "driver_fee": driver_fee
            }
        ]
    }


def valid_opening_hour(day="monday", starts_at="10:00:00", ends_at="12:00:00"):
    return {
        "day": day,
        "starts_at": starts_at,
        "ends_at": ends_at
    }


def valid_opening_hours():
    return \
        [
            valid_opening_hour("sunday", "2:00:00", "23:00:00"),
        ]


def opening_hours_opens_everyday():
    return [
        valid_opening_hour("monday", "01:00:00", "23:59:59"),
        valid_opening_hour("tuesday", "01:00:00", "23:59:59"),
        valid_opening_hour("wednesday", "01:00:00", "23:59:59"),
        valid_opening_hour("thursday", "01:00:00", "23:59:59"),
        valid_opening_hour("friday", "01:00:00", "23:59:59"),
        valid_opening_hour("saturday", "01:00:00", "23:59:59"),
        valid_opening_hour("sunday", "01:00:00", "23:59:59")
    ]


def valid_venue_data(company=None, title=None, address=None, opening_hours=None, opens_everyday=False, closed_everyday=False):
    from ..utils import Manager

    if not title:
        title = f"venue {uuid.uuid4()}"

    if not company:
        company = Manager.create_company()

    if address is None:
        address = valid_address_data()

    if opening_hours is None:
        opening_hours = valid_opening_hours()

    if opens_everyday:
        opening_hours = opening_hours_opens_everyday()

    if closed_everyday:
        opening_hours = []

    return {
        "company": company.id,
        "title": title,
        "phone_country_code": "+353",
        "phone_number": "123456789",
        "address": address,
        "description": "description",
        "opening_hours": opening_hours
    }


def valid_staff_data(company_member=None, venue=None):
    from ..utils import Manager

    if not company_member and not venue:
        venue = Manager.create_venue()
        company_member = Manager.create_company_member(company=venue.company)

    if not company_member:
        company_member = Manager.create_company_member(company=venue.company)

    if not venue:
        venue = Manager.create_venue(company_member.company)

    return {
        "company_member": company_member.user.id,
        "venue": venue.id
    }


def valid_category_data(parent=None, title=None, image=None):
    from ..utils import Manager
    if not title:
        title = f"category {str(uuid.uuid4())[:4]}"

    if not image:
        image = Manager.create_image()

    data = {
        "title": title,
        "image": image.id
    }

    if parent:
        data.update({"parent": parent.id})
    return data


def valid_item_data(title=None, subcategory=None, image=None, description="description"):
    from ..utils import Manager

    if not title:
        title = f"title {str(uuid.uuid4())[:4]}"

    if not image:
        image = Manager.create_image()

    if not subcategory:
        subcategory = Manager.create_subcategory()

    return {
        "title": title,
        "image": image.id,
        "subcategory": subcategory.id,
        "description": description
    }


def valid_menu_category_data(menu=None, category=None, include_passcode=False):
    from ..utils import Manager

    if not category:
        category = Manager.create_category()

    if not menu:
        menu = Manager.create_venue().menu

    data = {
        "menu": menu.venue_id,
        "category": category.id
    }

    if include_passcode:
        data.update({
            "passcode": menu.venue.company.passcode
        })

    return data


def valid_menu_item_data(menu=None, menu_category=None, item=None, subcategory=None, price=1000, price_sale=None):
    from ..utils import Manager

    if not menu:
        menu = Manager.create_venue().menu

    if not subcategory and item:
        subcategory = item.subcategory

    if not menu_category and menu.categories.count() == 0:
        category = subcategory.parent if subcategory else None
        menu_category = Manager.create_menu_category(menu=menu, category=category)

    if not menu_category:
        menu_category = menu.categories.first()

    if not subcategory:
        subcategory = Manager.create_subcategory(parent=menu_category.category)

    if not item:
        item = Manager.create_item(subcategory=subcategory)

    return {
        "menu": menu.venue_id,
        "menu_category": menu_category.id,
        "item": item.id,
        "price": price,
        "price_sale": price_sale,
        "currency": Manager.get_currency_euro().id,
    }


def valid_card_data(payment_method_id="pm_card_visa", default=True):
    return {
        "source": payment_method_id,
        "default": default
    }


def declined_card_data():
    return {
        "source": "pm_card_chargeDeclinedFraudulent",
        "default": False
    }


def action_required_card_data():
    return {
        "source": "pm_card_authenticationRequired",
        "default": False
    }


def insufficent_funds_card_data():
    return {
        "source": "pm_card_authenticationRequiredChargeDeclinedInsufficientFunds",
        "default": False
    }


def valid_webhook_data():
    import os
    return {
      "id": "evt_1Kkv0O2fgxhFyEMVvkRbRdC3",
      "object": "event",
      "account": "acct_1KW0in2fgxhFyEMV",
      "api_version": "2020-08-27",
      "created": 1649098319,
      "data": {
        "object": {
          "id": "acct_1KW0in2fgxhFyEMV",
          "object": "account",
          "business_profile": {
            "mcc": "5734",
            "name": "buss",
            "support_address": {
              "city": None,
              "country": None,
              "line1": None,
              "line2": None,
              "postal_code": None,
              "state": None
            },
            "support_email": "begum+test@gmail.com",
            "support_phone": "+353111111111",
            "support_url": None,
            "url": "google.com"
          },
          "capabilities": {
            "bancontact_payments": "active",
            "card_payments": "active",
            "eps_payments": "active",
            "giropay_payments": "active",
            "ideal_payments": "active",
            "p24_payments": "active",
            "sepa_debit_payments": "active",
            "sofort_payments": "active",
            "transfers": "active"
          },
          "charges_enabled": True,
          "controller": {
            "type": "application",
            "is_controller": True
          },
          "country": "IE",
          "default_currency": "eur",
          "details_submitted": True,
          "email": "begum+test@gmail.com",
          "payouts_enabled": True,
          "settings": {
            "bacs_debit_payments": {
            },
            "branding": {
              "icon": None,
              "logo": None,
              "primary_color": None,
              "secondary_color": None
            },
            "card_issuing": {
              "tos_acceptance": {
                "date": None,
                "ip": None
              }
            },
            "card_payments": {
              "statement_descriptor_prefix": "BUS"
            },
            "dashboard": {
              "display_name": "Google",
              "timezone": "Etc/UTC"
            },
            "payments": {
              "statement_descriptor": "GOOGLE.COM",
              "statement_descriptor_kana": None,
              "statement_descriptor_kanji": None
            },
            "sepa_debit_payments": {
            },
            "payouts": {
              "debit_negative_balances": True,
              "schedule": {
                "delay_days": 7,
                "interval": "daily"
              },
              "statement_descriptor": None
            }
          },
          "type": "standard",
          "created": 1645545374,
          "external_accounts": {
            "object": "list",
            "data": [
              {
                "id": "ba_1KW0mx2fgxhFyEMVThuB45h6",
                "object": "bank_account",
                "account": "acct_1KW0in2fgxhFyEMV",
                "account_holder_name": None,
                "account_holder_type": None,
                "account_type": None,
                "available_payout_methods": [
                  "standard"
                ],
                "bank_name": "STRIPE TEST BANK",
                "country": "IE",
                "currency": "eur",
                "default_for_currency": True,
                "fingerprint": "5ZRwZdzPwkP4vsEf",
                "last4": "5678",
                "metadata": {
                },
                "routing_number": "110000000",
                "status": "new"
              }
            ],
            "has_more": False,
            "total_count": 1,
            "url": "/v1/accounts/acct_1KW0in2fgxhFyEMV/external_accounts"
          },
          "future_requirements": {
            "alternatives": [
            ],
            "current_deadline": None,
            "currently_due": [
            ],
            "disabled_reason": None,
            "errors": [
            ],
            "eventually_due": [
            ],
            "past_due": [
            ],
            "pending_verification": [
            ]
          },
          "metadata": {
          },
          "requirements": {
            "alternatives": [
            ],
            "current_deadline": None,
            "currently_due": [
            ],
            "disabled_reason": None,
            "errors": [
            ],
            "eventually_due": [
            ],
            "past_due": [
            ],
            "pending_verification": [
            ]
          }
        },
        "previous_attributes": {
          "business_profile": {
            "name": None,
            "support_address": None,
            "support_email": None
          }
        }
      },
      "livemode": False,
      "pending_webhooks": 1,
      "request": {
        "id": None,
        "idempotency_key": None
      },
      "type": "account.updated"
    }


def valid_setting_data(key=Constants.SETTING_KEY_MINIMUM_ORDER_AMOUNT, value="50"):
    return {
        "key": key,
        "value": value
    }


def valid_order_item_data(menu_item=None, quantity=1, menu=None):
    from ..utils import Manager

    if not menu_item:
        menu_item = Manager.create_menu_item(menu=menu)

    return {
        "id": menu_item.id,
        "quantity": quantity
    }


def valid_order_items_data(menu=None, quantity=1):
    items_data = []

    for i in range(0, quantity):
        item = valid_order_item_data(menu=menu)
        items_data.append(item)

    return items_data


def valid_order_data(customer=None, company=None, venue=None, order_items=None, address=None, card=None, tip=0, include_delivery_fee=True):
    from ..utils import Manager

    if not customer:
        customer = Manager.create_customer()

    if not card:
        card = Manager.create_card(Manager.get_access_token(customer.user))

    if not venue:
        venue = Manager.create_venue(company=company, data=valid_venue_data(company, opens_everyday=True))

    company = venue.company

    if not company.stripe_account_id:
        Stripe.payments_enabled_account(company)

    if not order_items:
        order_items = valid_order_items_data(venue.menu, 1)

    if not address and not customer.address:
        Manager.add_address_to_customer(customer)

    address = address if address else customer.address

    expected_price = calculate_payment_values_for(order_items, venue, customer, tip, include_delivery_fee)["expected_price"]

    return {
        "venue": venue.id,
        "menu": venue.id,
        "address": address.id,
        "payment": {
            "card": card.id,
            "expected_price": expected_price,
            "tip": tip
        },
        "items": order_items
    }


def calculate_payment_values_for(order_items, venue, customer, tip, include_delivery_fee=True):
    from ...menu_item.models import MenuItem
    from ..utils import Manager
    from ...utils import Distance
    expected_price = 0
    subtotal = 0

    for order_item in order_items:
        menu_item = MenuItem.objects.get(id=order_item["id"])
        price = menu_item.price_sale if menu_item.price_sale is not None else menu_item.price
        subtotal += price * int(order_item["quantity"])

    service_fee_percentage = venue.service_fee_percentage
    service_fee = int(round(subtotal * service_fee_percentage))

    if service_fee < 50:
        service_fee = 50

    if service_fee > 200:
        service_fee = 200

    delivery_fee = 0
    driver_fee = 0

    if include_delivery_fee:
        distance = Distance.between(venue.address.point, customer.address.point, True)
        delivery_distance = Manager.get_delivery_distance_for(distance)
        driver_fee = delivery_distance.driver_fee
        delivery_fee = delivery_distance.fee

    expected_price = subtotal + service_fee + delivery_fee + tip

    return {
        "subtotal": subtotal,
        "expected_price": expected_price,
        "delivery_fee": delivery_fee,
        "service_fee": service_fee,
        "driver_fee": driver_fee
    }

