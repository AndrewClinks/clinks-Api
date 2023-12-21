from django.db.models import Prefetch

from ..menu_category.models import MenuCategory
from ..menu_item.models import MenuItem
from ..utils.Serializers import serializers, ListModelSerializer

from ..menu_category.serializers import MenuCategoryDetailSerializer


from .models import Menu


class MenuDetailSerializer(ListModelSerializer):
    menu_categories = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = ["menu_categories"]

    def get_menu_categories(self, instance):
        menu_categories = instance.categories.all().order_by("order").prefetch_related(
            "items__item__image", "items__item__subcategory"
        )
        return MenuCategoryDetailSerializer(menu_categories, many=True).data
