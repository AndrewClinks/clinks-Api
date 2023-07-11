from ..utils.Serializers import serializers, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from ..image.serializers import ImageDetailSerializer

from ..category.serializers import CategoryListSerializer, CategoryOrderDetailSerializer

from .models import Item


class ItemCreateSerializer(CreateModelSerializer):

    class Meta:
        model = Item
        exclude = ["sales_count"]

    def validate_subcategory(self, subcategory):
        if subcategory.parent is None:
            self.raise_validation_error("Subcategory", "It has to be a subcategory")
        return subcategory

    def create(self, validated_data):
        title = validated_data['title']

        item, created = Item.objects.get_or_create(title__iexact=title, defaults={**validated_data})

        Item.update_item_count_for(item.subcategory)

        return item


class ItemEditSerializer(EditModelSerializer):

    class Meta:
        model = Item
        exclude = ["sales_count", ]

    def validate_subcategory(self, subcategory):
        if subcategory.parent is None:
            self.raise_validation_error("Subcategory", "It has to be a subcategory")
        return subcategory

    def validate(self, attrs):
        title = attrs.get("title", None)

        if title and title != self.instance.title and Item.objects.filter(title__iexact=title):
            self.raise_validation_error("Item", "An item with this title exists already")

        return attrs

    def update(self, instance, validated_data):
        subcategory_old = instance.subcategory
        item = super(ItemEditSerializer, self).update(instance, validated_data)

        if "subcategory" in validated_data:
            Item.update_item_count_for(subcategory_old)
            Item.update_item_count_for(item.subcategory)

        return item


class ItemListSerializer(ListModelSerializer):
    image = ImageDetailSerializer()
    subcategory = CategoryListSerializer()
    menu_item = serializers.SerializerMethodField()

    class Meta:
        model = Item
        exclude = ["sales_count"]

    def get_select_related_fields(self):
        return ["image", "subcategory"]

    def get_menu_item(self, instance):
        menu_item_id = getattr(instance, "menu_item_id", None)
        if not menu_item_id:
            return None

        from ..menu_item.serializers import MenuItemLowestPriceSerializer, MenuItem
        menu_item = MenuItem.objects.filter(id=instance.menu_item_id).first()
        return MenuItemLowestPriceSerializer(menu_item).data


class ItemMenuListSerializer(ListModelSerializer):
    image = ImageDetailSerializer()
    subcategory = CategoryListSerializer()

    class Meta:
        model = Item
        fields = ["id", "title", "image", "description", "subcategory"]

    def get_select_related_fields(self):
        return ["image", "subcategory", ]


class ItemAdminListSerializer(ListModelSerializer):
    image = ImageDetailSerializer()

    class Meta(ListModelSerializer):
        model = Item
        fields = "__all__"

    def get_select_related_fields(self):
        return ["image", ]


class ItemAdminDetailSerializer(ItemAdminListSerializer):
    subcategory = CategoryOrderDetailSerializer()


class ItemOrderDetailSerializer(ListModelSerializer):
    image = ImageDetailSerializer()
    subcategory = CategoryOrderDetailSerializer()

    class Meta:
        model = Item
        fields = ["id", "title", "image", "description", "subcategory"]

    def get_select_related_fields(self):
        return ["image", "subcategory", ]