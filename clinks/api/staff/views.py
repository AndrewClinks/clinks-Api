from __future__ import unicode_literals

from django.db import transaction
from django.db.models import Q

from rest_framework.response import Response

from rest_framework import status

from django.shortcuts import (get_object_or_404, )

from .serializers import *

from ..utils.Permissions import (
    IsAdminPermission,
    IsCompanyMemberPermission
)

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView

from ..utils import QueryParams, Constants, Body


class ListCreate(SmartPaginationAPIView):
    permission_classes = [IsAdminPermission | IsCompanyMemberPermission]

    model = Staff
    list_serializer = StaffListSerializer
    detail_serializer = StaffDetailSerializer
    create_serializer = StaffCreateSerializer

    def add_filters(self, queryset, request):
        company_id = QueryParams.get_int(request, "company_id")
        venue_id = QueryParams.get_int(request, "venue_id")

        if self.is_admin_request() and not (venue_id or company_id):
            self.raise_exception("'company_id' or 'venue_id' is required")

        if self.is_company_member_request():
            queryset = queryset.filter(venue__company=self.get_company_member_from_request().company)

        if company_id and not self.is_company_member_request():
            queryset = queryset.filter(venue__company_id=company_id)

        if venue_id:
            queryset = queryset.filter(venue_id=venue_id)

        return queryset

    def override_post_data(self, request, data):
        if data and self.is_company_member_request():
            data["current_company_member"] = self.get_company_member_from_request()

        return data

    @transaction.atomic
    def delete(self, request):
        company_member_id = Body.get_int(request, "company_member_id", raise_exception=True)
        venue_id = Body.get_int(request, "venue_id", raise_exception=True)

        staff = get_object_or_404(Staff, company_member__user_id=company_member_id, venue_id=venue_id)

        if self.is_company_member_request() and staff.company_member.company != self.get_company_member_from_request().company:
            return self.respond_with("You cannot delete this staff", status_code=status.HTTP_400_BAD_REQUEST)

        staff.company_member.active_venue = None
        staff.company_member.save()
        staff.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class Delete(SmartDetailAPIView):
    permission_classes = [IsAdminPermission | IsCompanyMemberPermission]

    model = Staff
    deletable = True

    def queryset(self, request, id):
        queryset = Staff.objects.filter(id=id)

        if self.is_company_member_request():
            return queryset.filter(company_member__company=self.get_company_member_from_request().company)

        return queryset

    def handle_delete(self, instance):
        instance.company_member.active_venue = None
        instance.company_member.save()

        return super(Delete, self).handle_delete(instance)

