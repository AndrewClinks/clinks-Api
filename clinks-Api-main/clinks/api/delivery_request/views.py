from __future__ import unicode_literals

from .models import DeliveryRequest

from .serializers import *

from ..utils.Permissions import (
    IsDriverPermission

)

from django.db.models import Q

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView, CustomPagination

from ..utils import Constants, Token, QueryParams


class List(SmartPaginationAPIView):
    permission_classes = [IsDriverPermission]

    pagination_class = CustomPagination(ordering=("order_id"))

    model = DeliveryRequest
    list_serializer = DeliveryRequestListSerializer

    def queryset(self, request):
        return DeliveryRequest.objects.filter(driver=self.get_driver_from_request())

    def add_filters(self, queryset, request):
        # Get requests that are pending or accepted for current driver, if no accepted default to pending
        status = QueryParams.get_enum(request, "status", [Constants.DELIVERY_REQUEST_STATUS_PENDING, Constants.DELIVERY_REQUEST_STATUS_ACCEPTED], Constants.DELIVERY_REQUEST_STATUS_PENDING)
        last_rejected_order_id = QueryParams.get_int(request, "last_rejected_order_id")
        if status:
            queryset = queryset.filter(status=status)

        # This filters out all orders ids before the rejected
        # TODO: be more intelligent and only filter out the rejected order
        # Because what if there are lots of orders and rejecting the current blocks them from older still activeo ones
        if last_rejected_order_id:
            queryset = queryset.filter(order_id__gt=last_rejected_order_id)

        return queryset


class Detail(SmartDetailAPIView):
    permission_classes = [IsDriverPermission]

    model = DeliveryRequest
    edit_serializer = DeliveryRequestEditSerializer
    detail_serializer = DeliveryRequestDetailSerializer

    def queryset(self, request, id):
        return DeliveryRequest.objects.filter(id=id, driver=self.get_driver_from_request())

    def override_patch_data(self, request, data):
        data["driver"] = self.get_driver_from_request()
        return data
