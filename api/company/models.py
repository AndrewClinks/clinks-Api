from django.db import models

from ..image.models import Image

from ..utils.Fields import EnumField

from ..utils import Constants

from ..utils.Models import SmartModel

from ..utils import Slug

import random

import logging

logger = logging.getLogger(__name__)


class Company(SmartModel):

    id = models.AutoField(primary_key=True)

    title = models.CharField(max_length=255)

    slug = models.SlugField(unique=True)

    featured_image = models.OneToOneField(Image, related_name="company_as_featured", null=True, on_delete=models.SET_NULL)

    logo = models.OneToOneField(Image, related_name="company_as_logo", null=True, on_delete=models.SET_NULL)

    eircode = models.CharField(max_length=255)

    vat_no = models.CharField(max_length=255)

    liquor_license_no = models.CharField(max_length=255)

    status = EnumField(options=Constants.COMPANY_STATUSES, default=Constants.COMPANY_STATUS_SETUP_NOT_COMPLETED)

    has_added_menu_items = models.BooleanField(default=False)

    stripe_account_id = models.CharField(max_length=255, null=True)

    stripe_verification_status = EnumField(options=Constants.STRIPE_VERIFICATION_STATUSES)

    stripe_charges_enabled = models.BooleanField(default=False)

    stripe_payouts_enabled = models.BooleanField(default=False)

    total_earnings = models.PositiveIntegerField(default=0)

    sales_count = models.PositiveIntegerField(default=0)

    average_delivery_time = models.PositiveIntegerField(default=0)

    total_delivery_time = models.PositiveIntegerField(default=0)

    delivered_order_count = models.PositiveIntegerField(default=0)

    total_accept_time = models.PositiveIntegerField(default=0)

    average_accept_time = models.PositiveIntegerField(default=0)

    venue_count = models.PositiveIntegerField(default=0)

    passcode = models.PositiveIntegerField()

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Company {}: ".format(self.id)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = Slug.generate(self, 'title', 'slug')

        if not self.passcode:
            self.passcode = random.randint(1000, 9999)

        super(Company, self).save()

    def can_accept_payments(self):
        # For regular orders, validate Stripe account and charges enabled
        return self.stripe_account_id is not None and self.stripe_charges_enabled

    def update_stats_for(self, order):
        from ..utils import Constants, DateUtils
        from django.db.models import F

        if order.status == Constants.ORDER_STATUS_PENDING:
            self.sales_count = F("sales_count") + 1
            self.total_earnings = F("total_earnings") + order.payment.amount

        if order.status == Constants.ORDER_STATUS_LOOKING_FOR_DRIVER:
            accept_time = DateUtils.minutes_between(order.created_at, DateUtils.now())
            self.total_accept_time = F("total_accept_time") + accept_time
            self.average_accept_time = (F("average_accept_time") + accept_time) / F("sales_count")

        if order.delivery_status == Constants.DELIVERY_STATUS_DELIVERED:
            delivery_time = DateUtils.minutes_between(order.collected_at, DateUtils.now())
            self.delivered_order_count = F("delivered_order_count") + 1
            self.total_delivery_time = F("total_delivery_time") + delivery_time
            self.average_delivery_time = self.total_delivery_time / self.delivered_order_count

        self.save()

    @staticmethod
    def exclude_stripe_incomplete(queryset, accessor):
        queryset = queryset.filter(**{f"{accessor}__stripe_account_id__isnull": False}, **{f"{accessor}__stripe_charges_enabled": True})
        return queryset

    @staticmethod
    def filter_with_passcode(view, request, queryset, passcode_accessor):
        from ..utils import Body, QueryParams

        first = queryset.first()

        if not first:
            return queryset

        passcode = QueryParams.get_int(request, "passcode", raise_exception=True)

        if first and queryset.values(passcode_accessor).first()[passcode_accessor] != passcode:
            view.raise_exception("Incorrect passcode")

        return queryset.filter(**{f"{passcode_accessor}": passcode})


    @staticmethod
    def validate_passcode(serializer, attrs, current_company_member):
        passcode = attrs.pop("passcode", None)

        if not current_company_member:
            return

        if current_company_member and not passcode:
            serializer.raise_validation_error("passcode", "Passcode is required")

        if current_company_member.company.passcode != passcode:
            serializer.raise_validation_error("passcode", "Incorrect passcode")
