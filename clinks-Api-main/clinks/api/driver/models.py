from django.db import models

from ..utils.Fields import EnumField
from ..utils import Constants

from ..delivery_request.models import DeliveryRequest
from ..user.models import User
from ..identification.models import Identification
from ..utils.Models import SmartModel

from django.contrib.gis.db.models import PointField


class Driver(SmartModel):

    user = models.OneToOneField(User, primary_key=True, related_name='driver',  on_delete=models.CASCADE)

    identification = models.ForeignKey(Identification, related_name="drivers", null=True, on_delete=models.SET_NULL)

    ppsn = models.CharField(max_length=255)

    vehicle_type = EnumField(options=Constants.VEHICLE_TYPES)

    vehicle_registration_no = models.CharField(max_length=255, null=True)

    order_count = models.PositiveIntegerField(default=0)

    delivered_order_count = models.PositiveIntegerField(default=0)

    total_earnings = models.PositiveIntegerField(default=0)

    average_delivery_time = models.PositiveIntegerField(default=0)

    total_delivery_time = models.PositiveIntegerField(default=0)

    total_accept_time = models.PositiveIntegerField(default=0)

    last_known_location = PointField(srid=4326, null=True)

    last_known_location_updated_at = models.DateTimeField(null=True)

    current_delivery_request = models.OneToOneField(DeliveryRequest, related_name="driver_as_current", null=True, on_delete=models.SET_NULL)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Driver {}: ".format(self.user.id)

    def has_ongoing_delivery(self):
        from ..order.models import Order
        ongoing_delivery = Order.objects.filter(driver=self, delivery_status__in=[Constants.DELIVERY_STATUS_PENDING,
                                                                                  Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY,
                                                                                  Constants.DELIVERY_STATUS_FAILED])

        return ongoing_delivery.exists()

    def update_stats_for_accepted_delivery_request(self, delivery_request):
        from ..utils import DateUtils
        from django.db.models import F

        accept_time = DateUtils.minutes_between(delivery_request.created_at, DateUtils.now())

        self.total_accept_time = F("total_accept_time") + accept_time
        self.order_count = F("order_count") + 1
        self.current_delivery_request = delivery_request

        self.save()

    def update_stats_for_delivered_order(self, order):
        from ..utils import DateUtils
        from django.db.models import F

        delivery_time = DateUtils.minutes_between(order.collected_at, DateUtils.now())

        self.delivered_order_count = F("delivered_order_count") + 1
        self.total_delivery_time = F("total_delivery_time") + delivery_time
        self.average_delivery_time = self.total_delivery_time / self.delivered_order_count
        self.save()


