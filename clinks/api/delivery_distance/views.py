from __future__ import unicode_literals

from .serializers import *

from ..utils.Permissions import (
    IsAdminPermission,
    IsCustomerPermission
)

from rest_framework import status
from rest_framework.response import Response

from django.db.models import Q

from ..utils import QueryParams

from ..utils.Views import SmartPaginationAPIView


class ListCreate(SmartPaginationAPIView):
    permission_classes = [IsAdminPermission]

    model = DeliveryDistance
    create_serializer = DeliveryDistanceBulkCreateSerializer
    detail_serializer = DeliveryDistanceBulkDetailSerializer

    default_page_size = 1

    def get(self, request):

        if not self.has_permission(request, "GET"):
            return self.get_permission_denied_response(request, "GET")

        queryset = self.queryset(request)

        queryset = self.add_filters(queryset, request)

        data = {"results":  DeliveryDistanceListSerializer(queryset, many=True).data}

        return Response(data, status=status.HTTP_200_OK)

    def has_permission(self, request, method):
        if request == "POST" and not self.is_admin_request():
            return False
        return True

    def add_filters(self, queryset, request):
        distance = QueryParams.get(request, "distance")

        if distance and self.is_customer_request():
            queryset = queryset.filter(starts_lte=distance, ends_gt=distance)

        return queryset