from __future__ import unicode_literals

from django.db import transaction
from django.db.models import Q

from rest_framework import status

from ..category.models import Category

from .serializers import *

from rest_framework import status

from ..utils.Permissions import (
    IsAdminPermission,
)

import csv, codecs, json
from ..job.models import Job

from rest_framework.response import Response

from ..utils.Views import SmartPaginationAPIView, SmartDetailAPIView, SmartAPIView, CustomPagination

from ..utils import QueryParams, Constants, Point, Nearby, DateUtils

from ..tasks import import_items_via_csv


class ListCreate(SmartPaginationAPIView):

    model = Item
    list_serializer = ItemListSerializer
    detail_serializer = ItemAdminDetailSerializer
    create_serializer = ItemCreateSerializer

    def has_permission(self, request, method):
        if method == "POST":
            return self.is_admin_request()
        return True

    def get_list_serializer(self, request, queryset):
        if self.is_admin_request() or self.is_company_member_request():
            return ItemAdminListSerializer
        return ItemListSerializer

    def add_filters(self, queryset, request):
        search_term = QueryParams.get_str(request, "search_term")
        order = QueryParams.get_str(request, "order")
        category_id = QueryParams.get_int(request, "category_id")
        subcategory_id = QueryParams.get_int(request, "subcategory_id")
        point = Point.get(request)
        open_now = QueryParams.get_bool(request, "open_now")
        has_menu_item = QueryParams.get_bool(request, "has_menu_item")

        if search_term:
            queryset = queryset.filter(Q(title__icontains=search_term) |
                                       Q(description__icontains=search_term) |
                                       Q(subcategory__title__icontains=search_term) |
                                       Q(subcategory__parent__title__icontains=search_term))

        subcategory = Category.objects.filter(id=category_id, parent__isnull=False).first()

        if subcategory:
            subcategory_id = subcategory.id
            category_id = subcategory.parent_id

        if category_id:
            queryset = queryset.filter(subcategory__parent_id=category_id)

        if subcategory_id:
            queryset = queryset.filter(subcategory_id=subcategory_id)

        if point and not (self.is_company_member_request() or self.is_admin_request()):
            queryset = Nearby.items(queryset, point)

        if order == "most_popular":
            self.paginator.ordering = "-sales_count"
            queryset = queryset.distinct("id", "sales_count")
        else:
            self.paginator.ordering = "id"
            queryset = queryset.distinct("id")

        if open_now:
            day = DateUtils.weekday()
            time = DateUtils.time(DateUtils.now(True))
            queryset = queryset.filter(menu_items__menu__venue__opening_hours__day__iexact=day,
                                       menu_items__menu__venue__opening_hours__starts_at__lte=time,
                                       menu_items__menu__venue__opening_hours__ends_at__gt=time,
                                       menu_items__menu__venue__opening_hours__deleted_at__isnull=True)

        if not (self.is_company_member_request() or self.is_admin_request()):
            from django.db.models import OuterRef, Subquery
            from ..menu_item.models import MenuItem

            subquery = MenuItem.objects.filter(item_id=OuterRef("id"))
            subquery = subquery.order_by("price_sale", "price")
            subquery = MenuItem.add_customer_filters(subquery, point, open_now)

            queryset = queryset.annotate(menu_item_id=Subquery(subquery.values("id")[:1]))

            if has_menu_item:
                queryset = queryset.exclude(menu_item_id__isnull=True)

        return queryset


class EditDelete(SmartDetailAPIView):
    permission_classes = [IsAdminPermission]

    model = Item
    detail_serializer = ItemAdminDetailSerializer
    edit_serializer = ItemEditSerializer

    deletable = True

    def handle_delete(self, instance):
        if instance.menu_item_count > 0:
            return self.respond_with("This item has associated menu items. It can't be deleted",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        response = super(EditDelete, self).handle_delete(instance)

        Item.update_item_count_for(instance.subcategory)

        return response


class Import(SmartAPIView):
    permission_classes = [IsAdminPermission]

    @transaction.atomic
    def post(self, request):
        if not self.is_admin_request():
            return self.respond_with("You do not have permission to access this",
                                     status_code=status.HTTP_403_FORBIDDEN)

        if 'csv' not in request.FILES:
            return self.respond_with("Please include a 'csv' file", status_code=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["csv"]

        if file.content_type != "text/csv":
            return self.respond_with("File type is not 'csv'", status_code=status.HTTP_400_BAD_REQUEST)

        csv_file = csv.DictReader(codecs.iterdecode(file, 'utf-8'), delimiter=',')

        list_ = list(csv_file)

        if len(list_) == 0:
            return self.respond_with("File is empty", status_code=status.HTTP_400_BAD_REQUEST)

        keys = list_[0].keys()

        if "Title" not in keys:
            return self.respond_with("File is missing 'Title' column",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        if "Description (can be empty)" not in keys:
            return self.respond_with("File is missing 'Description' column",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        if "Image url (.jpg or .png only)" not in keys:
            return self.respond_with("File is missing 'Image url' column",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        if "Category" not in keys:
            return self.respond_with("File is missing 'Category' column",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        if "Subcategory" not in keys:
            return self.respond_with("File is missing 'Subcategory' column",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        csv_file = csv.DictReader(codecs.iterdecode(file, 'utf-8'), delimiter=',')

        rows = []
        for row in csv_file:
            row_data = {
                "title": row['Title'].replace('\r\n', '').strip(),
                "description": row["Description (can be empty)"],
                "category_title": row["Category"].strip(),
                "subcategory_title":  row["Subcategory"].strip(),
                "image_url": row['Image url (.jpg or .png only)'].replace('\r\n', '').strip()
            }
            rows.append(row_data)

        data = {
            "rows": rows
        }

        job = Job.objects.create(data=json.dumps(data))

        import_items_via_csv.delay_on_commit(job.id, request.user.id)

        return Response(status=status.HTTP_204_NO_CONTENT)
