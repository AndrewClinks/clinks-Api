from django.db import models

from ..driver.models import Driver

from ..order.models import Order
from ..currency.models import Currency

from ..utils import Constants

from ..utils.Fields import EnumField

from ..utils.Models import SmartModel


class DriverPayment(SmartModel):

    id = models.AutoField(primary_key=True)

    driver = models.ForeignKey(Driver, related_name="payments", on_delete=models.CASCADE)

    order = models.ForeignKey(Order, related_name="driver_payments", on_delete=models.CASCADE)

    currency = models.ForeignKey(Currency, related_name="driver_payments", on_delete=models.CASCADE)

    amount = models.PositiveIntegerField()

    type = EnumField(options=Constants.DRIVER_PAYMENT_TYPES)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "DriverPayment {}: ".format(self.id)

    @staticmethod
    def create(order, type):
        from django.db.models import F
        payment = order.payment
        amount = payment.delivery_driver_fee
        driver = order.driver

        if type == Constants.DRIVER_PAYMENT_TYPE_DELIVERY:
            amount += payment.tip
            driver.total_earnings = F("total_earnings") + amount
            driver.save()

        driver_payment = DriverPayment.objects.create(driver=driver, order=order, currency=payment.currency,
                                                      amount=amount, type=type)

        return driver_payment
