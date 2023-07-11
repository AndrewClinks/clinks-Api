from rest_framework.exceptions import APIException

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Personalization, Email)

from ..utils import Api, Message, DateUtils

from ..user.models import User

import random

SendGrid = SendGridAPIClient(Api.SENDGRID_API_KEY)

HEADERS = {
    'Authorization': "Bearer {}".format(Api.SENDGRID_API_KEY),
    'Content-Type': "application/json"
}


def send_code(user_id):
    user = User.objects.get(id=user_id)
    user.verification_code = generate_random_number(4)
    user.save()

    mail = Mail(
        from_email=Api.EMAIL_FROM,
        to_emails=user.email,
        subject='Password Reset Request',
        html_content='Hi {},<br><br><b>{}</b> is your password reset code'.format(user.first_name, user.verification_code))

    _send_email(mail)


def send_account_verification_code(user_id):
    user = User.objects.get(id=user_id)
    user.verification_code = generate_random_number(4)
    user.save()

    mail = Mail(
        from_email=Api.EMAIL_FROM,
        to_emails=user.email,
        subject='Account Verification',
        html_content='Hi {},<br><br><b>{}</b> is your account verification code'.format(user.first_name, user.verification_code))

    _send_email(mail)


def send_import_items_skipped_rows(skipped_rows, current_user_email):

    content = "Hi, Here is the skipped rows: <br><br>"

    for skipped in skipped_rows:
        content += f"Row no: {skipped['row']}: {skipped['reason']} <br>"

    mail = Mail(
        from_email=Api.EMAIL_FROM,
        to_emails=current_user_email,
        subject='Items Import Issue',
        html_content=content
    )

    _send_email(mail)


def send_return(order_id):
    from ..venue_payment.models import VenuePayment
    from ..driver_payment.models import DriverPayment
    from ..utils import Constants, Currency

    venue_payment = VenuePayment.objects.filter(order_id=order_id).first()
    order = venue_payment.order
    driver = order.driver

    symbol = venue_payment.currency.symbol
    content = f"Hi, <br>the following order has failed to be delivered and the goods are returned back to the venue<br><br> " \
              f"Order ID: {order_id} <br>" \
              f"Order Total: {Currency.format(order.payment.total, symbol)} <br>" \
              f"Vendor Net Received: {Currency.format(venue_payment.amount, symbol)} <br><br>" \
              f"Driver Name: {driver.user.first_name} {driver.user.last_name}<br>" \
              f"Driver Delivery Fee: {Currency.format(order.payment.delivery_fee, symbol)} <br>" \
              f"Driver Tip: {Currency.format(order.payment.tip, symbol)} <br>" \
              f"Driver Return Fee: {Currency.format(order.payment.delivery_fee, symbol)} <br><br>" \
              f"The driver's return fee has automatically been added to their Payment (in the Driver Payments table) " \
              f"however the Vendor's Net Received ({Currency.format(venue_payment.amount, symbol)}) must be collected " \
              f"from them off platform. <br><br>" \
              f"Thanks"

    mail = Mail(
        from_email=Api.EMAIL_FROM,
        to_emails=Api.RETURN_EMAILS,
        subject='Delivery Failed',
        html_content=content
    )

    _send_email(mail)


def generate_random_number(length):
    return int(''.join([str(random.randint(1, 9)) for _ in range(length)]))


def _send_email(mail):
    import os
    if os.environ.get("CI", False) == "true":
        return

    try:
        SendGrid.send(mail)
    except Exception as e:
        print(f"error while sending email with content: {mail.content}", e)
        raise APIException(Message.create(e))
