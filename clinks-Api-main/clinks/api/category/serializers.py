from ..utils.Serializers import serializers, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from ..image.serializers import ImageDetailSerializer

from .models import Category


class CategoryCreateSerializer(CreateModelSerializer):

    class Meta:
        model = Category
        exclude = ["sales_count", "menu_item_count", "item_count"]

    def create(self, validated_data):
        parent = validated_data.get("parent", None)
        title = validated_data['title']

        category, created = Category.objects.get_or_create(title__iexact=title, parent=parent, defaults={**validated_data})

        return category


class CategoryEditSerializer(EditModelSerializer):

    class Meta:
        model = Category
        exclude = ["sales_count", "menu_item_count", "item_count"]

    def validate(self, attrs):
        title = attrs.get("title", None)
        parent = attrs.get("parent", None)

        if parent and Category.objects.filter(parent=self.instance).exists():
            self.raise_validation_error("Category", "This category cannot have a parent since it has subcategories")

        if title and title != self.instance.title and Category.objects.filter(title__iexact=title):
            self.raise_validation_error("Category", "A category with this title exists already")

        return attrs


class CategoryListSerializer(ListModelSerializer):
    image = ImageDetailSerializer()

    class Meta:
        model = Category
        fields = ["id", "title", "image", "parent", "menu_item_count", "item_count"]


class CategoryAdminListSerializer(CategoryListSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta(CategoryListSerializer):
        model = Category
        fields = CategoryListSerializer.Meta.fields + ["sales_count", "subcategories", "menu_item_count", "item_count"]

    def get_subcategories(self, instance):
        subcategories = Category.objects.filter(parent_id=instance.id).order_by("title")
        return CategoryListSerializer(subcategories, many=True).data


class CategoryDetailSerializer(ListModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"


class CategoryTitleSerializer(ListModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title", "parent"]


class CategoryOrderDetailSerializer(ListModelSerializer):
    parent = CategoryTitleSerializer()

    class Meta:
        model = Category
        fields = ["id", "title", "parent"]


class SubcategoryMenuItemsDetailSerializer(ListModelSerializer):
    image = ImageDetailSerializer()
    menu_items = serializers.SerializerMethodField()
    menu_id = serializers.IntegerField(source="venue_id", read_only=True)

    class Meta(CategoryListSerializer):
        model = Category
        fields = ["id", "title", "image", "menu_id", "menu_items", "parent"]

    def get_select_related_fields(self):
        return ["image", ]

    def get_menu_items(self, instance):
        menu_id = getattr(instance, "menu_id", None)
        if not menu_id:
            return None

        from ..menu_item.serializers import MenuItem, MenuItemMenuListSerializer

        menu_items = MenuItem.objects.filter(menu_id=menu_id, item__subcategory_id=instance.id)

        return MenuItemMenuListSerializer(menu_items, many=True).data

