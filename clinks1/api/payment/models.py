from django.db import models

from ..utils import Constants

from ..customer.models import Customer
from ..currency.models import Currency
from ..company.models import Company

from ..utils.stripe import Payment as PaymentUtils

from ..card.models import Card

from ..utils.Models import SmartModel


class Payment(SmartModel):
    id = models.AutoField(primary_key=True)

    currency = models.ForeignKey(Currency, related_name="payments", on_delete=models.CASCADE)

    amount = models.PositiveIntegerField()

    tip = models.PositiveIntegerField(default=0)

    total = models.PositiveIntegerField()

    service_fee = models.PositiveIntegerField()

    delivery_driver_fee = models.PositiveIntegerField()

    delivery_fee = models.PositiveIntegerField()

    stripe_fee = models.PositiveIntegerField(default=0)

    stripe_charge_id = models.CharField(max_length=255, null=True)

    stripe_refund_id = models.CharField(max_length=255, null=True)

    stripe_return_charge_id = models.CharField(max_length=255, null=True)

    customer = models.ForeignKey(Customer, related_name="payments", on_delete=models.CASCADE)

    card = models.ForeignKey(Card, related_name="payments", null=True, on_delete=models.SET_NULL)

    company = models.ForeignKey(Company, related_name="payments", on_delete=models.CASCADE)

    paid_at = models.DateTimeField()

    refunded_at = models.DateTimeField(null=True)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Payment: {}".format(self.id)

    def refund(self):
        return PaymentUtils.refund(self)

    def returned(self, order):
        from ..driver_payment.models import DriverPayment
        from ..venue_payment.models import VenuePayment
        from ..tasks import send_mail

        venue_amount_to_be_paid = self.amount - self.stripe_fee

        DriverPayment.create(order, Constants.DRIVER_PAYMENT_TYPE_RETURN)
        VenuePayment.create(order, venue_amount_to_be_paid)

        send_mail.delay_on_commit("send_return", order.id)






