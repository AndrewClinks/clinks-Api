from django.db import models

from ..utils import Constants

from ..customer.models import Customer
from ..identification.models import Identification
from ..payment.models import Payment
from ..currency.models import Currency
from ..driver.models import Driver
from ..venue.models import Venue
from ..image.models import Image
from ..daily_stat.models import DailyStat
from django.contrib.gis.db.models import PointField

from ..utils.Fields import EnumField
from ..utils.Models import SmartModel


class Order(SmartModel):

    id = models.AutoField(primary_key=True)

    customer = models.ForeignKey(Customer, related_name="orders", on_delete=models.CASCADE)

    driver = models.ForeignKey(Driver, related_name="orders", null=True, on_delete=models.SET_NULL)

    venue = models.ForeignKey(Venue, related_name="orders", on_delete=models.CASCADE)

    payment = models.OneToOneField(Payment, related_name="order", on_delete=models.CASCADE)

    status = EnumField(options=Constants.ORDER_STATUSES, default=Constants.ORDER_STATUS_PENDING)

    delivery_status = EnumField(options=Constants.DELIVERY_STATUSES, default=Constants.DELIVERY_STATUS_PENDING)

    identification = models.OneToOneField(Identification, related_name="order", null=True, on_delete=models.SET_NULL)

    identification_status = EnumField(options=Constants.ORDER_IDENTIFICATION_STATUSES, null=True, default=None)

    no_answer_image = models.ForeignKey(Image, related_name="order_as_no_answer_image", null=True, on_delete=models.SET_NULL)

    no_answer_driver_location = PointField(srid=4326, null=True)

    started_looking_for_drivers_at = models.DateTimeField(null=True)

    accepted_at = models.DateTimeField(null=True)

    collected_at = models.DateTimeField(null=True)

    rejected_at = models.DateTimeField(null=True)

    failed_at = models.DateTimeField(null=True)

    returned_at = models.DateTimeField(null=True)

    delivered_at = models.DateTimeField(null=True)

    data = models.JSONField()

    driver_verification_number = models.PositiveIntegerField()

    rejection_reason = EnumField(options=Constants.ORDER_REJECTION_REASONS, null=True, default=None)

    receipt = models.CharField(max_length=255, null=True)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Order: {}".format(self.id)

    def accepted(self, delivery_request):
        from ..utils import DateUtils
        from ..tasks import send_notification

        self.driver = delivery_request.driver
        self.accepted_at = DateUtils.now()
        self.status = Constants.ORDER_STATUS_ACCEPTED

        self.save()

        self.driver.update_stats_for_accepted_delivery_request(delivery_request)

        send_notification.delay_on_commit("send_order_for_customer", self.id, self.status)

    def redact_customer(self):
        if self.identification:
            print("---")
            self.identification.delete()
            self.identification = None

        self.data["customer_address"] = "redacted_address"

        self.save()




