from __future__ import unicode_literals

from .models import Card

from rest_framework import status

from .serializers import (
    CardCreateSerializer,
    CardEditSerializer,
    CardListSerializer,
    CardDetailSerializer
)

from ..utils.Permissions import (
    IsCustomerPermission,
)


from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView, CustomPagination, CursorSetPagination


class ListCreate(SmartPaginationAPIView):
    permission_classes = [IsCustomerPermission, ]

    model = Card
    list_serializer = CardListSerializer
    detail_serializer = CardDetailSerializer
    create_serializer = CardCreateSerializer

    pagination_class = CustomPagination(ordering=("-default", "-created_at"))

    def add_filters(self, queryset, request):
        queryset = queryset.filter(customer=self.get_customer_from_request())

        return queryset

    def override_post_data(self, request, data):
        data["customer"] = self.request.user.id
        return data


class Edit(SmartDetailAPIView):
    permission_classes = [IsCustomerPermission, ]

    model = Card
    edit_serializer = CardEditSerializer
    detail_serializer = CardDetailSerializer
    deletable = True
    partial = False

    def queryset(self, request, id):
        queryset = Card.objects.filter(id=id, customer=self.get_customer_from_request())
        return queryset

    def handle_delete(self, instance):
        if instance.default:
            return self.respond_with("You cannot delete the default card", status_code=status.HTTP_400_BAD_REQUEST)

        return super(Edit, self).handle_delete(instance)











