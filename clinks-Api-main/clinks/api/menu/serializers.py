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
        menu_categories = MenuCategory.objects.filter(menu=instance).order_by("order").prefetch_related(
            Prefetch("items", queryset=MenuItem.objects.select_related("item__image", "item__subcategory"))
        )
        return MenuCategoryDetailSerializer(menu_categories, many=True).data
