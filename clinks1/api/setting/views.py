from __future__ import unicode_literals

from rest_framework import status

from .serializers import *

from ..utils.Permissions import (
    IsAdminPermission,
    IsCustomerPermission
)

from django.db.models import Q

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView

from ..utils import Constants, Token, QueryParams


class ListCreate(SmartPaginationAPIView):

    model = Setting
    detail_serializer = SettingDetailSerializer
    list_serializer = SettingListSerializer
    create_serializer = SettingCreateSerializer

    def add_filters(self, queryset, request):
        key = QueryParams.get_enum(request, "key", Constants.SETTING_KEYS)

        if key is None and self.is_customer_request():
            self.raise_exception("'key' filter is required")

        if key:
            queryset = queryset.filter(key__iexact=key)

        return queryset

    def has_permission(self, request, method):
        if method == "POST" and not self.is_admin_request():
            return False

        if self.is_driver_request() or self.is_company_member_request():
            return False

        return True
