import stripe
from ...utils import Api

stripe.api_key = Api.STRIPE_SECRET_KEY


def get_account(account_id):
    try:
        return stripe.Account.retrieve(
            account_id,
        )
    except Exception as e:
        return None


def get_event(id, account_id=None, on_platform=False):

    extra = {}
    if not on_platform:
        extra["stripe_account"] = account_id

    try:
        event = stripe.Event.retrieve(
            id,
            **extra
        )
        return event.data.object
    except Exception as e:
        return None


def handle_webhook_event(request, default_verification_status="pending"):
    from django.shortcuts import (get_object_or_404, )
    from ...company.models import Company

    account_id = request.data["account"]
    account = get_account(account_id)

    if len(account.requirements.eventually_due) == 0:
        verification_status = "verified"
    else:
        verification_status = default_verification_status

    company = get_object_or_404(Company, stripe_account_id=account_id)

    company.stripe_verification_status = verification_status
    company.stripe_charges_enabled = account.charges_enabled
    company.stripe_payouts_enabled = account.payouts_enabled
    company.save()

    return company
