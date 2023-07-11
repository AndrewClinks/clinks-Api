from django.db import models

from ..customer.models import Customer

from ..utils.Models import SmartModel


class Card(SmartModel):

    id = models.AutoField(primary_key=True)

    customer = models.ForeignKey(Customer, related_name="cards", on_delete=models.CASCADE)

    last4 = models.CharField(max_length=4)

    brand = models.CharField(max_length=255)

    expiry_month = models.IntegerField()
    expiry_year = models.IntegerField()

    name = models.CharField(max_length=255, null=True)

    default = models.BooleanField(default=False)

    stripe_payment_method_id = models.CharField(max_length=255)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Card {}".format(self.id)



