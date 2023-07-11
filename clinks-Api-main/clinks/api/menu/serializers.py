from ..utils.Serializers import serializers, ListModelSerializer

from ..menu_category.serializers import MenuCategoryDetailSerializer


from .models import Menu


class MenuDetailSerializer(ListModelSerializer):
    menu_categories = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = ["menu_categories"]

    def get_menu_categories(self, instance):
        menu_categories = instance.categories.all().order_by("order")
        return MenuCategoryDetailSerializer(menu_categories, many=True).data
