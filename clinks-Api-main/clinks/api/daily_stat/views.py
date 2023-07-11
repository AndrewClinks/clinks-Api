from __future__ import unicode_literals

from .models import DailyStat

from rest_framework import status

from rest_framework.response import Response

from django.db.models import Q

from ..utils.Permissions import (
    IsAdminPermission,
)

from ..utils import QueryParams, Constants, DateUtils, StatUtils

from ..utils.Views import SmartAPIView


class List(SmartAPIView):
    permission_classes = [IsAdminPermission, ]

    def get(self, request):
        return_total_stats = QueryParams.get_bool(request, "total")
        return_company_stats = QueryParams.get_bool(request, "company")
        return_platform_stats = QueryParams.get_bool(request, "platform")
        return_driver_stats = QueryParams.get_bool(request, "driver")

        company_id = QueryParams.get_int(request, "company_id")
        min_date = QueryParams.get_date(request, "min_date", DateUtils.last_week().date())
        max_date = QueryParams.get_date(request, "max_date", DateUtils.today().date())

        if max_date > DateUtils.next_month().date():
            return self.respond_with("'max_date' cannot be in the future",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        if DateUtils.date_in_future(min_date):
            return self.respond_with("'min_date' cannot be in the future",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        if max_date < min_date:
            return self.respond_with("'max_date' cannot be less than 'min_date'", status_code=status.HTTP_400_BAD_REQUEST)

        data = {}
        if return_total_stats:
            data["total"] = DailyStat.get_stats(Constants.DAILY_STAT_TYPE_TOTAL_EARNINGS, min_date, max_date)

        if return_company_stats:
            data["company"] = DailyStat.get_stats(Constants.DAILY_STAT_TYPE_TOTAL_COMPANY_EARNINGS, min_date, max_date, company_id=company_id)

        if return_driver_stats:
            data["driver"] = DailyStat.get_stats(Constants.DAILY_STAT_TYPE_TOTAL_DRIVER_EARNINGS, min_date, max_date)

        if return_platform_stats:
            data["platform"] = DailyStat.get_stats(Constants.DAILY_STAT_TYPE_PLATFORM_EARNINGS, min_date, max_date)

        return Response(data, status=status.HTTP_200_OK)

