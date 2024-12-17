from __future__ import unicode_literals

from .models import Customer

from .serializers import (
    CustomerCreateSerializer,
    CustomerEditSerializer,
    CustomerListSerializer,
    CustomerDetailSerializer
)

from ..utils.Permissions import (
    IsCustomerPermission,
    IsAdminPermission
)
from rest_framework.response import Response

from rest_framework import status

from django.db.models import Q

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView

import uuid

from ..utils import Constants, Token, QueryParams


class ListCreate(SmartPaginationAPIView):

    model = Customer
    detail_serializer = CustomerDetailSerializer
    list_serializer = CustomerListSerializer
    create_serializer = CustomerCreateSerializer

    def post_response(self, request, instance, data):
        data = {}
        if self.is_anonymous_request():
            student = instance
            data[Constants.CUSTOMER] = CustomerDetailSerializer(student).data
            data[Constants.USER_AUTH_TOKENS] = Token.create(student.user)

        return super(ListCreate, self).post_response(request, instance, data)

    def has_permission(self, request, method):
        if method == "CREATE" and not self.is_anonymous_request():
            return False

        if method == "GET" and (self.is_anonymous_request() or not self.is_admin_request()):
            return False

        return True

    def add_filters(self, queryset, request):
        search_term = QueryParams.get_str(request, "search_term")

        if search_term:
            queryset = queryset.filter(Q(user__first_name__icontains=search_term) |
                                       Q(user__last_name__icontains=search_term) |
                                       Q(user__email__icontains=search_term))

        return queryset


class Detail(SmartDetailAPIView):
    permission_classes = [IsCustomerPermission | IsAdminPermission]

    model = Customer
    detail_serializer = CustomerDetailSerializer
    edit_serializer = CustomerEditSerializer

    deletable = True

    def queryset(self, request, id):
        if self.is_customer_request():
            return Customer.objects.filter(user_id=request.user.id)

        return Customer.objects.filter(user_id=id)

    def has_permission(self, request, method):
        if method == "PATCH" or method == "DELETE":
            return self.is_customer_request()

        return True

    def handle_delete(self, instance):
        from ..order.models import Order

        if Order.objects.filter(status__in=[Constants.ORDER_STATUS_PENDING, Constants.ORDER_STATUS_LOOKING_FOR_DRIVER]).exists():
            return self.respond_with("You cannot delete your account while there is an active order/s")

        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)




