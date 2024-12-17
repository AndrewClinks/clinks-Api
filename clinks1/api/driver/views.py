from __future__ import unicode_literals

from .models import Driver

from .serializers import *

from ..utils.Permissions import (
    IsAdminPermission,
    IsDriverPermission

)

from django.db.models import Q

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView

from ..utils import Constants, Token, QueryParams


class ListCreate(SmartPaginationAPIView):
    permission_classes = [IsAdminPermission]

    model = Driver
    detail_serializer = DriverAdminDetailSerializer
    list_serializer = DriverListSerializer
    create_serializer = DriverCreateSerializer

    def add_filters(self, queryset, request):
        search_term = QueryParams.get_str(request, "search_term")

        if search_term:
            queryset = queryset.filter(Q(user__first_name__icontains=search_term) |
                                       Q(user__last_name__icontains=search_term) |
                                       Q(user__email__icontains=search_term))

        return queryset


class Detail(SmartDetailAPIView):
    permission_classes = [IsAdminPermission | IsDriverPermission]

    model = Driver
    detail_serializer = DriverDetailSerializer
    edit_serializer = DriverAdminEditSerializer

    deletable = True

    def queryset(self, request, id):
        if self.is_driver_request():
            return Driver.objects.filter(user_id=request.user.id)

        return Driver.objects.filter(user_id=id)

    def has_permission(self, request, method):
        if method == "DELETE":
            return self.is_admin_request()

        return True

    def handle_delete(self, instance):
        # todo check if driver has active order otherwise don't delete it
        instance.user.soft_delete()

        response = super(Detail, self).handle_delete(instance)

        AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_DRIVER_COUNT, Driver.objects.count(), True)

        return response

    def get_detail_serializer(self, request, instance):
        if self.is_driver_request():
            return DriverDetailSerializer

        return DriverAdminDetailSerializer

    def get_edit_serializer(self, request, instance):
        if self.is_driver_request():
            return DriverEditSerializer
        return DriverAdminEditSerializer
