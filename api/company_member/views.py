from __future__ import unicode_literals

from django.db import transaction
from django.db.models import Q

from rest_framework import status

from .models import CompanyMember

from .serializers import (
    CompanyMemberCreateSerializer,
    CompanyMemberEditSerializer,
    CompanyMemberAdminEditSerializer,
    CompanyMemberListSerializer,
    CompanyMemberDetailSerializer
)

from ..utils.Permissions import (
    IsAdminPermission,
    IsCompanyMemberPermission
)

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView

from ..utils import QueryParams, Injection


class ListCreate(SmartPaginationAPIView):
    permission_classes = [IsAdminPermission | IsCompanyMemberPermission]

    model = CompanyMember
    list_serializer = CompanyMemberListSerializer
    detail_serializer = CompanyMemberDetailSerializer
    create_serializer = CompanyMemberCreateSerializer

    def override_post_data(self, request, data):
        if self.is_company_member_request():
            data["company"] = self.get_company_member_from_request().company.id

        return data

    def add_filters(self, queryset, request):
        search_term = QueryParams.get_str(request, "search_term")
        company_id = QueryParams.get_int(request, "company_id")

        if self.is_company_member_request():
            queryset = queryset.filter(company=self.get_company_member_from_request().company)

        if search_term:
            queryset = queryset.filter(Q(user__first_name__icontains=search_term) |
                                       Q(user__last_name__icontains=search_term) |
                                       Q(user__email__icontains=search_term))

        if company_id:
            queryset = queryset.filter(company_id=company_id)

        return queryset

    def paginated_response(self, queryset, serializer_class):
        queryset = Injection.add_venue_ids_to_company_members(queryset)
        response = super(ListCreate, self).paginated_response(queryset, serializer_class)
        return response


class Detail(SmartDetailAPIView):
    permission_classes = [IsAdminPermission | IsCompanyMemberPermission]

    model = CompanyMember
    detail_serializer = CompanyMemberDetailSerializer
    edit_serializer = CompanyMemberEditSerializer

    def queryset(self, request, id):
        if self.is_company_member_staff_request():
            return CompanyMember.objects.filter(user_id=request.user.id)

        queryset = CompanyMember.objects.filter(user_id=id)

        if self.is_company_member_admin_request():
            return queryset.filter(company=self.get_company_member_from_request().company)

        return queryset

    def get_edit_serializer(self, request, instance):
        serializer_class = CompanyMemberEditSerializer if self.is_company_member_request() else CompanyMemberAdminEditSerializer
        return serializer_class(
            instance=instance,
            data=request.data,
            partial=getattr(self, 'partial', True),  # Default to `partial=True` if not explicitly set
            context={'request': request}
        )
