from django.db import models

from ..utils.Models import SmartModel

from ..utils.Fields import EnumField

from ..utils import Constants


class AllTimeStat(SmartModel):

    id = models.AutoField(primary_key=True)

    type = EnumField(options=Constants.ALL_TIME_STAT_TYPES)

    value = models.PositiveIntegerField(default=0)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return f"All Time Stat: {self.type}: {self.value}"

    @staticmethod
    def get(type):
        if type not in Constants.ALL_TIME_STAT_TYPES:
            raise Exception(f"type must be one of {Constants.ALL_TIME_STAT_TYPES}")

        queryset = AllTimeStat.objects.filter(type=type)
        if not queryset.exists():

            return 0

        return queryset.first().value

    @staticmethod
    def update_for(order):
        from ..utils import DateUtils
        if order.status == Constants.ORDER_STATUS_PENDING:
            AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_TOTAL_EARNINGS, order.payment.total)
            AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_TOTAL_COMPANY_EARNINGS, order.payment.amount)
            AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_TOTAL_DRIVER_EARNINGS, order.payment.tip + order.payment.delivery_driver_fee)
            AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_PLATFORM_EARNINGS, order.payment.service_fee)
            AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_SALES_COUNT, 1)

        if order.status == Constants.ORDER_STATUS_REJECTED:
            AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_REJECTED_ORDER_COUNT, 1)

        if order.delivery_status == Constants.DELIVERY_STATUS_DELIVERED:
            delivered_order_count_stat = AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_DELIVERED_ORDER_COUNT, 1).value
            wait_time = DateUtils.minutes_between(order.created_at, DateUtils.now())
            total_wait_time_stat = AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_TOTAL_WAIT_TIME, wait_time).value
            AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_AVERAGE_WAIT_TIME, total_wait_time_stat/delivered_order_count_stat, True)

    @staticmethod
    def update(type, value, should_reset_to_value=False):
        from django.db.models import F
        all_time_stat = AllTimeStat.objects.filter(type=type).first()

        if not all_time_stat:
            all_time_stat = AllTimeStat.objects.create(type=type, value=value)
            return all_time_stat

        if should_reset_to_value:
            all_time_stat.value = value
        else:
            all_time_stat.value = F("value") + value

        all_time_stat.save()

        return all_time_stat
