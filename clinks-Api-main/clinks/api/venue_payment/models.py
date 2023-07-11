from django.db import models

from ..venue.models import Venue
from ..order.models import Order
from ..currency.models import Currency

from ..utils import Constants

from ..utils.Fields import EnumField

from ..utils.Models import SmartModel


class VenuePayment(SmartModel):

    id = models.AutoField(primary_key=True)

    venue = models.ForeignKey(Venue, related_name="venue_payments", on_delete=models.CASCADE)

    order = models.ForeignKey(Order, related_name="venue_payments", on_delete=models.CASCADE)

    currency = models.ForeignKey(Currency, related_name="venue_payments", on_delete=models.CASCADE)

    amount = models.PositiveIntegerField()

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "VenuePayment {}: ".format(self.id)

    @staticmethod
    def create(order, amount):
        data = {
            "venue": order.venue,
            "order": order,
            "currency": order.payment.currency,
            "amount": amount
        }

        venue_payment = VenuePayment.objects.create(**data)

        return venue_payment
