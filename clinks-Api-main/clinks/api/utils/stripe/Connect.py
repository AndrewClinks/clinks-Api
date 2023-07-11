import stripe, json

from ...card.models import Card

from ..stripe import Card

from ...utils import Message, Api, Exception as CustomException
from rest_framework import status

stripe.api_key = Api.STRIPE_SECRET_KEY


def create_account(customer, source):
    stripe_account = stripe.Customer.create(
        name=f"{customer.user.first_name} {customer.user.last_name}",
        email=customer.user.email,
        description="Customer for {}".format(customer.user.email),
    )

    customer.stripe_customer_id = stripe_account.id
    customer.save()

    card = Card.create(customer, source, True)

    return card


def _create_standard_account(company):
    try:
        account = stripe.Account.create(type="standard")
    except Exception as e:
        raise CustomException.raiseError({"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

    data = json.loads(str(account))

    company.stripe_account_id = data["id"]
    company.save()

    return company


def get_standard_connect_activation_link(company, refresh_url=None, return_url=None):
    if not company.stripe_account_id:
        _create_standard_account(company)

    stripe_account = stripe.Account.retrieve(company.stripe_account_id)

    if len(stripe_account.requirements.eventually_due) != 0:
        return _get_standard_connect_activation_link(company, refresh_url, return_url)

    company.stripe_verification_status = "verified"
    company.save()

    return None


def _get_standard_connect_activation_link(company, refresh_url=None, return_url=None):
    link = stripe.AccountLink.create(
        account=company.stripe_account_id,
        refresh_url=refresh_url,
        return_url=return_url,
        type="account_onboarding",
    )

    response_json = json.loads(str(link))

    return response_json["url"]

