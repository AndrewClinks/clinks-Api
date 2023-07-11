from __future__ import unicode_literals

from django.db import transaction
from django.db.models import Q

from rest_framework import status

from .models import Admin

from .serializers import (
    AdminCreateSerializer,
    AdminEditSerializer,
    AdminSuperEditSerializer,
    AdminListSerializer,
    AdminDetailSerializer
)

from ..utils.Permissions import (
    IsAdminPermission,
    IsSuperAdminPermission
)

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView

from ..utils import QueryParams, Constants


class ListCreate(SmartPaginationAPIView):
    permission_classes = [IsAdminPermission]

    model = Admin
    list_serializer = AdminListSerializer
    detail_serializer = AdminDetailSerializer
    create_serializer = AdminCreateSerializer

    def has_permission(self, request, method):
        if method == "POST":
            return self.is_super_admin_request()

        return True


class Detail(SmartDetailAPIView):

    model = Admin
    detail_serializer = AdminDetailSerializer
    edit_serializer = AdminEditSerializer

    permission_classes = [IsAdminPermission]

    deletable = True

    def queryset(self, request, id):
        if self.is_admin_staff_request():
            return Admin.objects.filter(user_id=request.user.id)

        return Admin.objects.filter(user_id=id)

    def has_permission(self, request, method):
        if method == "DELETE":
            return self.is_super_admin_request()
        return True

    def get_edit_serializer(self, request, instance):
        if self.is_super_admin_request() and instance.user.id != self.request.user.id:
            return AdminSuperEditSerializer

        return AdminEditSerializer

    def handle_delete(self, instance):
        if instance.user.id == self.request.user.id or instance.role == Constants.ADMIN_ROLE_ADMIN:
            return self.respond_with("You cannot delete this account", status_code=status.HTTP_400_BAD_REQUEST)

        instance.user.soft_delete()
        return super(Detail, self).handle_delete(instance)