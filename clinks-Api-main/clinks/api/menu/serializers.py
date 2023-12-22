from .models import Menu
from ..menu_category.serializers import MenuCategoryDetailSerializer, MenuCategoriesDetailSerializer
from ..utils.Serializers import serializers, ListModelSerializer


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


class MenuCategoriesSerializer(ListModelSerializer):
    menu_categories = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = ["menu_categories"]

    def get_menu_categories(self, instance):
        menu_categories = instance.categories.all().order_by("order")
        return MenuCategoriesDetailSerializer(menu_categories, many=True).data
