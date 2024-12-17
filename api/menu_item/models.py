from django.db import models

from ..menu.models import Menu
from ..item.models import Item
from ..menu_category.models import MenuCategory
from ..currency.models import Currency

from ..utils import Constants

from ..utils.Models import SmartModel


class MenuItem(SmartModel):

    id = models.AutoField(primary_key=True)

    item = models.ForeignKey(Item, related_name="menu_items", on_delete=models.CASCADE)

    menu_category = models.ForeignKey(MenuCategory, related_name="items", on_delete=models.CASCADE)

    menu = models.ForeignKey(Menu, related_name="items", on_delete=models.CASCADE)

    currency = models.ForeignKey(Currency, related_name="items", on_delete=models.CASCADE)

    price = models.PositiveIntegerField()

    price_sale = models.PositiveIntegerField(null=True)

    order = models.PositiveIntegerField()

    sales_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "MenuItem {}: ".format(self.id)

    @staticmethod
    def update_menu_item_count_for(item):
        item.menu_item_count = MenuItem.objects.filter(item=item).count()
        item.save()

        subcategory = item.subcategory
        subcategory.menu_item_count = MenuItem.objects.filter(item__subcategory=item.subcategory).count()
        subcategory.save()

        category = subcategory.parent
        category.menu_item_count = MenuItem.objects.filter(item__subcategory__parent_id=subcategory.parent_id).count()
        category.save()

    @staticmethod
    def update_sales_count_for(order):
        from django.db.models import F
        from ..category.models import Category
        from ..utils import List
        menu_items = order.data["items"]

        items_to_update = []
        categories_to_update = []
        subcategories_to_update = []

        for menu_item in menu_items:
            item = menu_item["item"]
            subcategory = item["subcategory"]
            category = subcategory["parent"]

            items_to_update.append(item)
            subcategories_to_update.append(subcategory)
            categories_to_update.append(category)

        menu_items_with_occurrences = List.count_occurrence(menu_items, "id")
        items_with_occurrences = List.count_occurrence(items_to_update, "id")
        categories_with_occurrences = List.count_occurrence(subcategories_to_update, "id")
        subcategories_with_occurrences = List.count_occurrence(categories_to_update, "id")

        for data in menu_items_with_occurrences:
            item = MenuItem.objects.get(id=data["item"]["id"])
            item.sales_count = F("sales_count") + data["occurrence"]
            item.save()

        for data in items_with_occurrences:
            item = Item.objects.get(id=data["item"]["id"])
            item.sales_count = F("sales_count") + data["occurrence"]
            item.save()

        for data in categories_with_occurrences:
            item = Category.objects.get(id=data["item"]["id"])
            item.sales_count = F("sales_count") + data["occurrence"]
            item.save()

        for data in subcategories_with_occurrences:
            item = Category.objects.get(id=data["item"]["id"])
            item.sales_count = F("sales_count") + data["occurrence"]
            item.save()

    @staticmethod
    def add_customer_filters(queryset, point=None, open_now=False):
        from ..utils import DateUtils, Nearby
        from ..company.models import Company

        queryset = Company.exclude_stripe_incomplete(queryset, "menu__venue__company")

        queryset = queryset.filter(menu__venue__company__status=Constants.COMPANY_STATUS_ACTIVE, menu__venue__paused=False)

        if point:
            queryset = Nearby.menu_items(queryset, point)

        if open_now:
            day = DateUtils.weekday()
            time = DateUtils.time(DateUtils.now(True))
            queryset = queryset.filter(menu__venue__opening_hours__day__iexact=day,
                                       menu__venue__opening_hours__starts_at__lte=time,
                                       menu__venue__opening_hours__ends_at__gt=time,
                                       menu__venue__opening_hours__deleted_at__isnull=True).distinct()

        return queryset


