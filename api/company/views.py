from __future__ import unicode_literals

from django.db import transaction
from django.db.models import Q

from rest_framework import status

from .models import Company

from .serializers import (
    CompanyCreateSerializer,
    CompanyEditSerializer,
    CompanyAdminEditSerializer,
    CompanyListSerializer,
    CompanyDetailSerializer,
    CompanyAdminDetailSerializer,
    CompanyAdminPasscodeDetailSerializer
)

from ..utils.Permissions import (
    IsAdminPermission,
    IsCompanyMemberPermission
)

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView

from ..utils import QueryParams, Constants


class ListCreate(SmartPaginationAPIView):
    permission_classes = [IsAdminPermission]

    model = Company
    list_serializer = CompanyListSerializer
    detail_serializer = CompanyDetailSerializer
    create_serializer = CompanyCreateSerializer

    def add_filters(self, queryset, request):
        search_term = QueryParams.get_str(request, "search_term")

        if search_term:
            queryset = queryset.filter(Q(title__icontains=search_term) |
                                       Q(members__user__first_name__icontains=search_term) |
                                       Q(members__user__last_name__icontains=search_term) |
                                       Q(members__user__email__icontains=search_term))

        queryset = queryset.distinct()

        return queryset


class Detail(SmartDetailAPIView):
    permission_classes = [IsAdminPermission | IsCompanyMemberPermission]

    model = Company
    detail_serializer = CompanyDetailSerializer
    edit_serializer = CompanyEditSerializer

    def queryset(self, request, id):
        if self.is_company_member_request():
            return Company.objects.filter(id=self.get_company_member_from_request().company_id)
        return Company.objects.filter(id=id)

    def get_edit_serializer(self, request, instance):
        serializer_class = CompanyEditSerializer if self.is_company_member_request() else CompanyAdminEditSerializer
        return serializer_class(
            instance=instance,
            data=request.data,
            partial=getattr(self, 'partial', True),  # Use `partial=True` by default if not set
            context={'request': request}
        )

    def get_detail_serializer(self, request, instance):
        if self.is_company_member_request():
            return CompanyDetailSerializer

        return_passcode = QueryParams.get_bool(request, "passcode")

        if return_passcode:
            return CompanyAdminPasscodeDetailSerializer

        return CompanyAdminDetailSerializer
