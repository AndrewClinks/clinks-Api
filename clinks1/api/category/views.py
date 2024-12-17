from __future__ import unicode_literals

from django.db import transaction
from django.db.models import Q

from rest_framework.response import Response

from rest_framework import status

from .serializers import *

from ..utils.Permissions import (
    IsAdminPermission,
)

from django.db.models.query import F

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView, CustomPagination

from ..utils import QueryParams, Constants, DateUtils


class ListCreate(SmartPaginationAPIView):
    pagination_class = CustomPagination(['title', '-created_at'])
    model = Category
    list_serializer = CategoryListSerializer
    detail_serializer = CategoryDetailSerializer
    create_serializer = CategoryCreateSerializer

    def has_permission(self, request, method):
        if method == "POST":
            return self.is_admin_request()
        return True

    def get_list_serializer(self, request, queryset):
        if self.is_admin_request():
            return CategoryAdminListSerializer

        extend_menu_items = QueryParams.get_bool(request, "extend_menu_items")
        venue_id = QueryParams.get_int(request, "venue_id")
        has_parent = QueryParams.get_bool(request, "has_parent", None)

        if extend_menu_items and venue_id and has_parent:
            return SubcategoryMenuItemsDetailSerializer

        return CategoryListSerializer

    def add_filters(self, queryset, request):
        search_term = QueryParams.get_str(request, "search_term")
        order = QueryParams.get_str(request, "order")
        has_parent = QueryParams.get_bool(request, "has_parent", None)
        parent_id = QueryParams.get_int(request, "parent_id")
        has_items = QueryParams.get_bool(request, "has_items")
        has_menu_items = QueryParams.get_bool(request, "has_menu_items")
        venue_id = QueryParams.get_int(request, "venue_id")
        extend_menu_items = QueryParams.get_bool(request, "extend_menu_items")

        if search_term:
            queryset = queryset.filter(title__icontains=search_term)

        if order == "most_popular":
            self.paginator.ordering = "-sales_count"
        else:
            self.paginator.ordering = ("title", "-created_at")

        if has_parent is not None:
            queryset = queryset.exclude(parent__isnull=has_parent)

        if parent_id is not None:
            queryset = queryset.filter(parent_id=parent_id)

        if has_items:
            queryset = queryset.filter(item_count__gt=0)

        if has_menu_items:
            queryset = queryset.filter(menu_item_count__gt=0)

        if venue_id and not has_parent:
            queryset = queryset.filter(menu_categories__menu__venue_id=venue_id)

        if venue_id and has_parent:
            queryset = queryset.filter(parent__menu_categories__menu__venue_id=venue_id)

        if extend_menu_items and venue_id and has_parent:
            queryset = queryset.annotate(menu_id=F("parent__menu_categories__menu"))

        return queryset


class EditDelete(SmartDetailAPIView):
    permission_classes = [IsAdminPermission]

    model = Category
    detail_serializer = CategoryDetailSerializer
    edit_serializer = CategoryEditSerializer

    deletable = True

    def has_permission(self, request, method):
        if method == "GET":
            return False
        return True

    def handle_delete(self, instance):
        from ..item.models import Item
        if instance.menu_item_count > 0:
            return self.respond_with("This category has associated menu items. It can't be deleted",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        instance.delete()

        if instance.parent is None:
            Category.objects.filter(parent=instance).update(deleted_at=DateUtils.now())
            Item.objects.filter(subcategory__parent=instance).update(deleted_at=DateUtils.now())
            instance.item_count = 0
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        Item.objects.filter(subcategory=instance).update(deleted_at=DateUtils.now())
        instance.parent.item_count = Item.objects.filter(subcategory__parent=instance.parent).count()
        instance.parent.save()

        return Response(status=status.HTTP_204_NO_CONTENT)



