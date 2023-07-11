import stripe, json

from rest_framework.exceptions import APIException

from ...card.models import Card

from ...utils import Message, Api

stripe.api_key = Api.STRIPE_SECRET_KEY


def create(customer, source, default):
    try:
        payment_method = stripe.PaymentMethod.attach(source, customer=customer.stripe_customer_id)
        card_data = {
            **payment_method.card,
            "id": payment_method.id
        }

    except Exception as error:
        raise APIException(Message.create(error))

    return _create(customer, card_data, default)


def _create(customer, card_data, default=False):
    card_data = {
        "customer": customer,
        "stripe_payment_method_id": card_data["id"],
        "name": card_data["name"] if "name" in card_data else None,
        "expiry_month": card_data["exp_month"],
        "expiry_year": card_data["exp_year"],
        "brand": card_data["brand"],
        "default": default,
        "last4": card_data["last4"]
    }

    card = Card.objects.create(**card_data)

    return card

