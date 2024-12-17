from django.db import models

from ..address.models import Address
from ..company.models import Company
from ..currency.models import Currency

from ..utils import Constants, Distance

from ..utils.Models import SmartModel

from ..utils import Slug, DateUtils


class Venue(SmartModel):

    id = models.AutoField(primary_key=True)

    title = models.CharField(max_length=255)

    slug = models.SlugField(unique=True)

    address = models.OneToOneField(Address, related_name="venue", on_delete=models.CASCADE)

    company = models.ForeignKey(Company, related_name="venues", on_delete=models.CASCADE)

    phone_country_code = models.CharField(max_length=255)

    phone_number = models.CharField(max_length=255)

    description = models.TextField(null=True)

    service_fee_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0.05)

    currency = models.ForeignKey(Currency, related_name="menus", null=True, on_delete=models.SET_NULL)

    total_earnings = models.PositiveIntegerField(default=0)

    sales_count = models.PositiveIntegerField(default=0)

    average_delivery_time = models.PositiveIntegerField(default=0)

    total_delivery_time = models.PositiveIntegerField(default=0)

    delivered_order_count = models.PositiveIntegerField(default=0)

    total_accept_time = models.PositiveIntegerField(default=0)

    paused = models.BooleanField(default=False)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Venue {}: ".format(self.id)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = Slug.generate(self, 'title', 'slug')

        super(Venue, self).save()

    def update_stats_on_create(self):
        from ..all_time_stat.models import AllTimeStat

        self.company.venue_count = Venue.objects.filter(company=self.company).count()
        self.company.save()

        AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_VENUE_COUNT, Venue.objects.count(), True)

    def open(self):
        weekday = DateUtils.weekday()
        now = DateUtils.now(True).time()
        opening_hour = self.opening_hours.filter(day__iexact=weekday, starts_at__lte=now, ends_at__gt=now)
        return opening_hour.exists()

    def can_deliver_to(self, address):
        from ..delivery_distance.models import DeliveryDistance

        max_delivery_distance = DeliveryDistance.max_delivery_distance()
        distance = Distance.between(self.address.point, address.point, True)

        return distance <= max_delivery_distance

    def update_stats_for(self, order):
        from ..utils import Constants
        from django.db.models import F

        if order.status == Constants.ORDER_STATUS_PENDING:
            self.sales_count = F("sales_count") + 1
            self.total_earnings = F("total_earnings") + order.payment.amount

        if order.status == Constants.ORDER_STATUS_LOOKING_FOR_DRIVER:
            accept_time = DateUtils.minutes_between(order.created_at, DateUtils.now())
            self.total_accept_time = F("total_accept_time") + accept_time

        if order.delivery_status == Constants.DELIVERY_STATUS_DELIVERED:
            delivery_time = DateUtils.minutes_between(order.collected_at, DateUtils.now())
            self.delivered_order_count = F("delivered_order_count") + 1
            self.total_delivery_time = F("total_delivery_time") + delivery_time
            self.average_delivery_time = self.total_delivery_time/self.delivered_order_count

        self.save()