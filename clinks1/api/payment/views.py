from __future__ import unicode_literals

from .serializers import *

from ..utils.Permissions import (
    IsAdminPermission,
)

from django.db.models import Q

from ..utils import QueryParams, Constants
from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView


class List(SmartPaginationAPIView):
    permission_classes = [IsAdminPermission]

    model = Payment
    list_serializer = PaymentListSerializer

    def add_filters(self, queryset, request):
        search_term = QueryParams.get_str(request, "search_term")
        order_status = QueryParams.get_enum(request, "order_status", [Constants.ORDER_STATUS_ACCEPTED, Constants.ORDER_STATUS_REJECTED])
        delivery_status = QueryParams.get_enum(request, "delivery_status", [Constants.DELIVERY_STATUS_RETURNED, Constants.DELIVERY_STATUS_DELIVERED])

        if order_status:
            queryset = queryset.filter(order__status=order_status)

        if delivery_status:
            queryset = queryset.filter(order__delivery_status=delivery_status)

        if search_term:
            queryset = queryset.filter(Q(company__title__icontains=search_term) |
                                       Q(customer__user__first_name__icontains=search_term) |
                                       Q(customer__user__last_name__icontains=search_term))

        return queryset