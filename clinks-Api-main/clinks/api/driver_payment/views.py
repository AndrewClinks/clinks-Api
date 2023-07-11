from __future__ import unicode_literals

from .serializers import *

from django.db.models import F, Sum

from ..utils.Permissions import (
    IsAdminPermission,
    IsDriverPermission
)

from django.db.models import Q

from rest_framework.response import Response
from rest_framework import status

from ..utils import QueryParams, Constants, DateUtils
from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView


class List(SmartPaginationAPIView):
    permission_classes = [IsAdminPermission | IsDriverPermission]

    model = DriverPayment
    list_serializer = DriverPaymentListSerializer

    def get(self, request):
        if not self.has_permission(request, "GET"):
            return self.get_permission_denied_response(request, "GET")

        queryset = self.queryset(request)

        queryset = self.add_filters(queryset, request)

        if not self.get_list_serializer(request, queryset):
            return self.get_missing_serializer_response(request, "GET")

        if self.is_admin_request():
            serializer_class = self.get_list_serializer(request, queryset)
            return self.paginated_response(queryset, serializer_class)

        data = {
            "count": queryset.count(),
            "total_earnings": queryset.aggregate(total_earnings=Sum('amount'))["total_earnings"],
            "total_tips": queryset.aggregate(total_tips=Sum("order__payment__tip"))["total_tips"],
            "currency": CurrencyListSerializer(queryset.first().currency).data if queryset.exists() else None
        }

        return Response(data, status=status.HTTP_200_OK)

    def add_filters(self, queryset, request):
        search_term = QueryParams.get_str(request, "search_term")
        type = QueryParams.get_enum(request, "type", Constants.DRIVER_PAYMENT_TYPES)
        min_date = QueryParams.get_date(request, "min_date")
        max_date = QueryParams.get_date(request, "max_date")

        if self.is_driver_request():
            queryset = queryset.filter(driver=self.get_driver_from_request())

            if min_date is None:
                min_date = DateUtils.today().date()

            if max_date is None:
                max_date = DateUtils.next_week(min_date)

            queryset = queryset.filter(created_at__gte=min_date, created_at__lte=max_date)

        if self.is_admin_request() and type:
            queryset = queryset.filter(type=type)

        if self.is_admin_request() and search_term:
            queryset = queryset.filter(Q(driver__user__first_name__icontains=search_term) |
                                       Q(driver__user__last_name__icontains=search_term))

        return queryset

