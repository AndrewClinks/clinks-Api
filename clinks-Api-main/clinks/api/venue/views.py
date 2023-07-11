from __future__ import unicode_literals

from django.db import transaction
from django.db.models import Q

from rest_framework import status

from .serializers import *

from ..utils.Permissions import (
    IsAdminPermission,
    IsCompanyMemberPermission,
    IsCustomerPermission
)

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView

from ..utils import QueryParams, Point, Nearby, DateUtils


class ListCreate(SmartPaginationAPIView):
    model = Venue
    list_serializer = VenueAdminListSerializer
    detail_serializer = VenueAdminDetailSerializer
    create_serializer = VenueCreateSerializer

    def override_post_data(self, request, data):
        if self.is_company_member_request():
            data["company"] = self.get_company_member_from_request().company.id

        return data

    def add_filters(self, queryset, request):
        search_term = QueryParams.get_str(request, "search_term")
        open_now = QueryParams.get_bool(request, "open_now")
        company_id = QueryParams.get_int(request, "company_id")
        point = Point.get(request)
        paused = QueryParams.get_bool(request, "paused", None)

        if self.is_company_member_request():
            queryset = queryset.filter(company=self.get_company_member_from_request().company)

        if self.is_admin_request() and company_id:
            queryset = queryset.filter(company_id=company_id)

        if paused is not None:
            queryset = queryset.filter(paused=paused)

        if search_term:
            queryset = queryset.filter(Q(title__icontains=search_term) |
                                       Q(description__icontains=search_term) |
                                       Q(address__line_1__icontains=search_term))

        if point:
            queryset = Nearby.venues(queryset, point)

        if open_now:
            day = DateUtils.weekday()
            time = DateUtils.time(DateUtils.now(True))
            queryset = queryset.filter(opening_hours__day__iexact=day,
                                       opening_hours__starts_at__lte=time,
                                       opening_hours__ends_at__gt=time,
                                       opening_hours__deleted_at__isnull=True)

        if self.is_customer_request() or self.is_anonymous_request():
            from ..company.models import Company
            queryset = Company.exclude_stripe_incomplete(queryset, "company")
            queryset = queryset.filter(paused=False)

        return queryset

    def has_permission(self, request, method):
        if self.is_driver_request():
            return False
        elif method == "POST" and not (self.is_admin_request() or self.is_company_member_request()):
            return False
        return True

    def get_list_serializer(self, request, queryset):
        if self.is_admin_request():
            return VenueAdminListSerializer
        elif self.is_company_member_request():
            return VenueMemberListSerializer
        return VenueCustomerListSerializer

    def get_detail_serializer(self, request, instance):
        if self.is_admin_request():
            return VenueAdminDetailSerializer
        return VenueMemberDetailSerializer

    def paginated_response(self, queryset, serializer_class):
        response = super(ListCreate, self).paginated_response(queryset, serializer_class)

        if self.is_customer_request() or self.is_anonymous_request():
            response.data["total_count"] = queryset.count()

        return response


class Detail(SmartDetailAPIView):

    model = Venue
    edit_serializer = VenueEditSerializer

    def queryset(self, request, id):
        queryset = Venue.objects.filter(id=id)

        if self.is_company_member_request():
            queryset = queryset.filter(company=self.get_company_member_from_request().company)

        return queryset

    def get_detail_serializer(self, request, instance):
        if self.is_admin_request():
            return VenueAdminDetailSerializer
        if self.is_company_member_request():
            return VenueMemberDetailSerializer
        return VenueCustomerDetailSerializer

    def has_permission(self, request, method):
        if self.is_driver_request():
            return False
        elif method == "PATCH" and not (self.is_admin_request() or self.is_company_member_request()):
            return False
        return True
