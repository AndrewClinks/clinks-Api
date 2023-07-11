from __future__ import unicode_literals

from django.db.models import Q

from .serializers import *

from ..utils.Permissions import (
    IsAdminPermission,
    IsCompanyMemberPermission
)

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView, CustomPagination

from ..utils import QueryParams, Constants, Point, Nearby, DateUtils


class ListCreate(SmartPaginationAPIView):
    pagination_class = CustomPagination(["order", 'created_at'])

    model = MenuItem
    list_serializer = MenuItemListSerializer
    detail_serializer = MenuItemDetailSerializer
    create_serializer = MenuItemCreateSerializer

    def has_permission(self, request, method):
        if method == "POST":
            return self.is_admin_request() or self.is_company_member_request()

        if self.is_driver_request():
            return False

        return True

    def override_post_data(self, request, data):
        if self.is_company_member_request():
            data["current_company_member"] = self.get_company_member_from_request()

        return data

    def add_filters(self, queryset, request):
        venue_id = QueryParams.get_int(request, "venue_id")
        item_id = QueryParams.get_int(request, "item_id")
        category_id = QueryParams.get_int(request, "category_id")
        subcategory_id = QueryParams.get_int(request, "subcategory_id")
        menu_id = QueryParams.get_int(request, "menu_id")
        search_term = QueryParams.get_str(request, "search_term")
        order = QueryParams.get_str(request, "order")
        point = Point.get(request)
        open_now = QueryParams.get_bool(request, "open_now")

        if self.is_company_member_request():
            queryset = queryset.filter(menu_category__menu__venue__company__members=self.get_company_member_from_request())

            Company.filter_with_passcode(self, request, queryset, "menu_category__menu__venue__company__passcode")

        if venue_id:
            queryset = queryset.filter(menu__venue_id=venue_id)

        if item_id:
            queryset = queryset.filter(item_id=item_id)

        if category_id:
            queryset = queryset.filter(menu_category__category_id=category_id)

        if subcategory_id:
            queryset = queryset.filter(item__subcategory_id=subcategory_id)

        if menu_id:
            queryset = queryset.filter(menu_id=menu_id)

        if search_term:
            queryset = queryset.filter(Q(item__title__icontains=search_term) |
                                       Q(item__description__icontains=search_term) |
                                       Q(item__subcategory__title__icontains=search_term) |
                                       Q(item__subcategory__parent__title__icontains=search_term))

        if order == "lowest_price":
            self.pagination_class = CustomPagination(["price_sale", "price", "order", "created_at"])

        if not (self.is_company_member_request() or self.is_admin_request()):
            queryset = MenuItem.add_customer_filters(queryset, point, open_now)

            if order == "closest":
                self.pagination_class = CustomPagination(["distance", "order", "created_at"])

        queryset = queryset.distinct()

        return queryset

    def get_list_serializer(self, request, queryset):
        if self.is_admin_request() or self.is_company_member_request():
            return MenuItemListSerializer
        return MenuItemCustomerListSerializer


class EditDelete(SmartDetailAPIView):
    permission_classes = [IsAdminPermission | IsCompanyMemberPermission]

    model = MenuItem
    detail_serializer = MenuItemDetailSerializer
    edit_serializer = MenuItemEditSerializer

    deletable = True

    def queryset(self, request, id):
        queryset = MenuItem.objects.filter(id=id)
        if self.is_company_member_request():
            queryset = queryset.filter(menu_category__menu__venue__company__members=self.get_company_member_from_request())

            queryset = Company.filter_with_passcode(self, request, queryset, "menu_category__menu__venue__company__passcode")

            return queryset
        return queryset

    def has_permission(self, request, method):
        if method == "GET":
            return False
        return True

    def handle_delete(self, instance):
        response = super(EditDelete, self).handle_delete(instance)

        MenuItem.update_menu_item_count_for(instance.item)

        return response
