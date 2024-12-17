from __future__ import unicode_literals

from .serializers import *

from ..utils.Permissions import (
    IsAdminPermission,
    IsCompanyMemberPermission
)

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView


class Create(SmartPaginationAPIView):
    permission_classes = [IsAdminPermission | IsCompanyMemberPermission]

    create_serializer = MenuCategoryCreateSerializer
    detail_serializer = MenuCategoryDetailSerializer

    def override_post_data(self, request, data):
        if self.is_company_member_request():
            data["current_company_member"] = self.get_company_member_from_request()

        return data


class Detail(SmartDetailAPIView):
    permission_classes = [IsAdminPermission | IsCompanyMemberPermission]

    model = MenuCategory
    detail_serializer = MenuCategoryDetailSerializer

    deletable = True

    def queryset(self, request, id):
        queryset = MenuCategory.objects.filter(id=id)

        if self.is_company_member_request():
            queryset = queryset.filter(menu__venue__company__members__user_id=self.request.user.id)

            queryset = Company.filter_with_passcode(self, request, queryset, "menu__venue__company__passcode")

            return queryset

        return queryset

