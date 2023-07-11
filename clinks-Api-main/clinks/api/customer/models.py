from django.db import models

from ..address.models import Address

from ..user.models import User
from ..identification.models import Identification
from ..utils.Models import SmartModel


class Customer(SmartModel):

    user = models.OneToOneField(User, primary_key=True, related_name='customer',  on_delete=models.CASCADE)

    identification = models.ForeignKey(Identification,  related_name="customers", null=True, on_delete=models.SET_NULL)

    address = models.OneToOneField(Address, related_name="customer", null=True, on_delete=models.SET_NULL)

    stripe_customer_id = models.CharField(max_length=255, null=True)

    last_order_at = models.DateTimeField(null=True)

    order_count = models.PositiveIntegerField(default=0)

    total_spending = models.PositiveIntegerField(default=0)

    average_spending_per_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Customer {}: ".format(self.user.id)

    def update_stats_for(self, order):
        from ..utils import DateUtils
        from django.db.models import F

        self.last_order_at = DateUtils.now()
        self.order_count = F("order_count") + 1
        self.total_spending = F("total_spending") + order.payment.total
        self.average_spending_per_order = self.total_spending/self.order_count

        self.save()

    def delete(self):
        self.user.redact()

        if self.address:
            self.address.redact()

        if self.identification:
            self.identification.delete()

        for order in self.orders.all():
            order.redact_customer()





