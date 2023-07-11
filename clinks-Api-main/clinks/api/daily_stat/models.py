from django.db import models

from ..utils.Models import SmartModel

from ..utils.Fields import EnumField

from ..venue.models import Venue
from ..company.models import Company

from ..utils import Constants, DateUtils, StatUtils


class DailyStat(SmartModel):

    id = models.AutoField(primary_key=True)

    date = models.DateField()

    type = EnumField(options=Constants.DAILY_STAT_TYPES)

    value = models.PositiveIntegerField(default=0)

    venue = models.ForeignKey(Venue, related_name="daily_stats", null=True, on_delete=models.SET_NULL)

    company = models.ForeignKey(Company, related_name="daily_stats", null=True, on_delete=models.SET_NULL)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return f"All Time Stat: {self.type}: {self.value}: {self.venue}"

    @staticmethod
    def update_for(order):
        DailyStat.update(Constants.DAILY_STAT_TYPE_TOTAL_EARNINGS, order.payment.total)
        DailyStat.update(Constants.DAILY_STAT_TYPE_TOTAL_COMPANY_EARNINGS, order.payment.amount, order.venue)
        DailyStat.update(Constants.DAILY_STAT_TYPE_TOTAL_DRIVER_EARNINGS, order.payment.tip + order.payment.delivery_driver_fee)
        DailyStat.update(Constants.DAILY_STAT_TYPE_PLATFORM_EARNINGS, order.payment.service_fee)
        DailyStat.update(Constants.DAILY_STAT_TYPE_SALES_COUNT, 1, order.venue)

    @staticmethod
    def update(type, value_to_be_added, venue=None):
        from django.db.models import F
        date = DateUtils.today().date()

        daily_stat = DailyStat.objects.filter(type=type, date=date).first()

        if not daily_stat:
            DailyStat.objects.create(type=type, date=date, value=value_to_be_added)
        else:
            daily_stat.value = F("value") + value_to_be_added
            daily_stat.save()

        if not venue:
            return

        daily_stat_venue = DailyStat.objects.filter(type=type, date=date, venue=venue).first()

        if not daily_stat_venue:
            DailyStat.objects.create(type=type, date=date, venue=venue, value=value_to_be_added)
        else:
            daily_stat_venue.value = F("value") + value_to_be_added
            daily_stat_venue.save()

        company = venue.company

        daily_stat_company = DailyStat.objects.filter(type=type, date=date, company=company).first()

        if not daily_stat_venue:
            DailyStat.objects.create(type=type, date=date, company=company, value=value_to_be_added)
            return

        daily_stat_company.value = F("value") + value_to_be_added
        daily_stat_company.save()

    @staticmethod
    def get_stats(type, min_date=None, max_date=None, company_id=None,):
        types = [type, Constants.DAILY_STAT_TYPE_SALES_COUNT]

        queryset = DailyStat.objects.filter(date__gte=min_date, date__lte=max_date, type__in=types)

        if company_id and type == Constants.DAILY_STAT_TYPE_TOTAL_COMPANY_EARNINGS:
            queryset = queryset.filter(venue__company__id=company_id)

        else:
            queryset = queryset.filter(venue__isnull=True, company__isnull=True)

        stats = DailyStat._to_list(queryset, types)

        return StatUtils.sort_list_multi(stats, min_date, max_date, ["earnings", Constants.DAILY_STAT_TYPE_SALES_COUNT])

    @staticmethod
    def _to_list(queryset, types):
        list_ = []
        queryset = queryset.values("date", "type", "value")
        for current in queryset:
            if current["type"] not in types:
                continue

            found_item = next((x for x in list_ if x["date"] == current["date"]), None)

            if current["type"] != Constants.DAILY_STAT_TYPE_SALES_COUNT:
                current["type"] = "earnings"

            if found_item is None:
                list_.append({
                    "date": current["date"],
                    f"{current['type']}": current["value"]
                })
                continue

            found_item[f"{current['type']}"] = current["value"]

        return list_
