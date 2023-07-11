from __future__ import unicode_literals

from .serializers import *

from django.shortcuts import get_object_or_404

from ..utils.Permissions import (
    IsCustomerPermission,
    IsAdminPermission,
    IsCompanyMemberPermission,
    IsAuthenticated
)

from django.db.models import Q

from ..utils import QueryParams, Constants, Receipt
from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView, SmartAPIView


class ListCreate(SmartPaginationAPIView):
    permission_classes = [IsCustomerPermission | IsAdminPermission | IsCompanyMemberPermission]

    model = Order
    create_serializer = OrderCreateSerializer
    detail_serializer = OrderCustomerDetailSerializer

    def override_post_data(self, request, data):
        if self.is_customer_request():
            data["customer"] = self.request.user.id

        return data

    def has_permission(self, request, method):
        if method == "POST" and not self.is_customer_request():
            return False
        return True

    def get_list_serializer(self, request, queryset):
        if self.is_customer_request():
            return OrderCustomerListSerializer
        elif self.is_company_member_request():
            return OrderCompanyMemberListSerializer
        return OrderAdminListSerializer

    def add_filters(self, queryset, request):
        statuses = QueryParams.get_enum_list(request, "statuses", Constants.ORDER_STATUSES)
        delivery_statuses = QueryParams.get_enum_list(request, "delivery_statuses", Constants.DELIVERY_STATUSES)
        rejection_reason = QueryParams.get_enum(request, "rejection_reason", Constants.ORDER_REJECTION_REASONS)
        driver_id = QueryParams.get_int(request, "driver_id")
        venue_id = QueryParams.get_int(request, "venue_id")
        customer_id = QueryParams.get_int(request, "customer_id")
        company_id = QueryParams.get_int(request, "company_id")
        search_term = QueryParams.get_str(request, "search_term")

        if self.is_company_member_request():
            queryset = queryset.filter(venue__active_members=self.get_company_member_from_request())

        if self.is_customer_request():
            queryset = queryset.filter(customer=self.get_customer_from_request())

        if statuses:
            queryset = queryset.filter(status__in=statuses)

        if delivery_statuses:
            queryset = queryset.filter(delivery_status__in=delivery_statuses)

        if rejection_reason:
            queryset = queryset.filter(rejection_reason=rejection_reason)

        if self.is_admin_request():
            if driver_id:
                queryset = queryset.filter(driver__user_id=driver_id)

            if customer_id:
                queryset = queryset.filter(customer__user_id=customer_id)

            if company_id:
                queryset = queryset.filter(venue__company_id=company_id)

        if venue_id and (self.is_customer_request() or self.is_admin_request()):
            queryset = queryset.filter(venue_id=venue_id)

        if search_term:
            queryset = queryset.filter(Q(venue__title__icontains=search_term) |
                                       Q(venue__company__title__icontains=search_term) |
                                       Q(customer__user__first_name__icontains=search_term) |
                                       Q(customer__user__last_name__icontains=search_term) |
                                       Q(driver__user__first_name__icontains=search_term) |
                                       Q(driver__user__last_name__icontains=search_term))

        return queryset

    def paginated_response(self, queryset, serializer_class):
        response = super(ListCreate, self).paginated_response(queryset, serializer_class)

        if self.is_company_member_request() or self.is_customer_request():
            response.data["total_count"] = queryset.count()

        return response


class Detail(SmartDetailAPIView):
    permission_classes = [IsAuthenticated]

    model = Order
    edit_serializer = OrderCompanyMemberEditSerializer
    detail_serializer = OrderCompanyMemberDetailSerializer

    def has_permission(self, request, method):
        if method == "PATCH" and not (self.is_company_member_request() or self.is_driver_request()):
            return False
        return True

    def queryset(self, request, id):
        queryset = Order.objects.filter(id=id)

        if self.is_customer_request():
            queryset = queryset.filter(customer=self.get_customer_from_request())

        if self.is_driver_request():
            queryset = queryset.filter(driver=self.get_driver_from_request())

        if self.is_company_member_request():
            queryset = queryset.filter(venue__staff__company_member=self.get_company_member_from_request())

        return queryset

    def get_edit_serializer(self, request, instance):
        if self.is_driver_request():
            return OrderDriverEditSerializer
        return OrderCompanyMemberEditSerializer

    def get_detail_serializer(self, request, instance):
        if self.is_customer_request():
            return OrderCustomerDetailSerializer
        elif self.is_driver_request():
            return OrderDriverDetailSerializer
        elif self.is_company_member_request():
            return OrderCompanyMemberDetailSerializer
        return OrderAdminDetailSerializer


