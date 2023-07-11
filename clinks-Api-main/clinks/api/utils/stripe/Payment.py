import stripe, json

from ...utils import Api, Exception as CustomException, DateUtils

stripe.api_key = Api.STRIPE_SECRET_KEY


def create_payment_intent(amount, currency, description, payment_method_id, account_id=None, on_platform=False,
                          application_fee_amount=None, stripe_customer_account_id=None):
    extra = {}
    if not on_platform:
        extra["stripe_account"] = account_id

        if application_fee_amount and application_fee_amount > 0:
            extra["application_fee_amount"] = application_fee_amount

        payment_method_id = get_connect_payment_method(payment_method_id, account_id, stripe_customer_account_id).id

    return stripe.PaymentIntent.create(
        amount=amount,
        currency=currency.code.lower(),
        description=description,
        payment_method_types=['card'],
        payment_method=payment_method_id,
        confirmation_method="manual",
        expand=["charges.data.balance_transaction"],
        **extra
    )


def get_payment_intent(payment_intent_id, account_id=None, on_platform=False):
    extra = {}
    if not on_platform:
        extra["stripe_account"] = account_id

    return stripe.PaymentIntent.retrieve(
        payment_intent_id,
        **extra
    )


def payment_intent_paid(payment_intent):
    return payment_intent.status == "succeeded"


def payment_intent_requires_user_action(payment_intent):
    return payment_intent.status in ["requires_action", "requires_source_action"] and payment_intent.next_action.type == "use_stripe_sdk"


def get_connect_payment_method(payment_method_id, stripe_account_id, stripe_customer_account_id):
    # grab a payment method that represents the shared customer model that we can use to charge on a connected account
    # using the connect payment method in the charge means it is created on the connected account, our stripe key is used so
    # we have access to the shared customer across all the customer accounts
    payment_method = stripe.PaymentMethod.create(
        customer=stripe_customer_account_id,
        payment_method=payment_method_id,
        stripe_account=stripe_account_id,
    )

    return payment_method


def charge(serializer, payment_intent_id, create_payment_intent_function, get_payment_intent_function=None, recurring_payment=False):
    from rest_framework import status

    if payment_intent_id:
        payment_intent = get_payment_intent_function() if get_payment_intent_function is not None else get_payment_intent(payment_intent_id)
    else:
        payment_intent = create_payment_intent_function()
    try:
        if not payment_intent.status == "succeeded":
            payment_intent.confirm()
    except Exception as error:
        serializer.raise_validation_error("Payment", str(error))

    if payment_intent_requires_user_action(payment_intent):
        data = {
            "payment_intent_id": payment_intent.id,
            "client_secret": payment_intent.client_secret,
            "requires_action": True,
            "recurring_payment": recurring_payment,
            "account_id": payment_intent.stripe_account
        }

        raise CustomException.raiseError(data, status.HTTP_200_OK)

    elif not payment_intent_paid(payment_intent):
        serializer.raise_validation_error("Payment",
                                    "An unexpected error occurred, you have not been charged, please try again")

    return payment_intent


def get_payment_data(payment_intent, account_id=None, on_platform=False):
    stripe_charge = payment_intent.charges.data[0]
    stripe_charge_data = json.loads(str(stripe_charge))
    stripe_charge_id = stripe_charge_data["id"]

    extra = {}
    if not on_platform:
        extra["stripe_account"] = account_id

    balance_transaction = stripe.BalanceTransaction.retrieve(
        stripe_charge_data["balance_transaction"],
        **extra
    )

    amount = stripe_charge_data["amount"]

    total_transaction_fee = round(balance_transaction["fee"])

    application_fee_amount = stripe_charge_data["application_fee_amount"]
    if not application_fee_amount:
        application_fee_amount = 0

    stripe_fee = total_transaction_fee - application_fee_amount

    data = {
        "total": amount,
        "stripe_charge_id": stripe_charge_id,
        "stripe_fee": stripe_fee,
    }

    return data


def refund(payment):
    stripe_account_id = payment.company.stripe_account_id

    stripe_refund = stripe.Refund.create(
        charge=payment.stripe_charge_id,
        stripe_account=stripe_account_id,
    )

    refund_data = json.loads(str(stripe_refund))
    refund_id = refund_data["id"]

    payment.refunded_at = DateUtils.now()
    payment.stripe_refund_id = refund_id

    payment.save()

    return payment
