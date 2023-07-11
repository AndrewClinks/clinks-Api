from ..utils.Serializers import serializers, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from ..utils import Constants
from ..menu_item.serializers import MenuItemMenuListSerializer
from ..category.serializers import CategoryListSerializer

from ..company_member.models import CompanyMember, Company

from .models import MenuCategory


class MenuCategoryCreateSerializer(CreateModelSerializer):
    current_company_member = serializers.PrimaryKeyRelatedField(queryset=CompanyMember.objects.all(), required=False)
    passcode = serializers.IntegerField(required=False)

    class Meta:
        model = MenuCategory
        exclude = ["order"]

    def validate_category(self, category):
        if category.parent is not None:
            self.raise_validation_error("MenuCategory", "Given category is a subcategory")

        return category

    def validate(self, attrs):
        menu = attrs["menu"]
        category = attrs["category"]
        current_company_member = attrs.pop("current_company_member", None)

        if MenuCategory.objects.filter(menu=menu, category=category).exists():
            self.raise_validation_error("MenuCategory", "A menu category with this category already exists")

        if current_company_member and current_company_member.company != menu.venue.company:
            self.raise_validation_error("MenuItem", "You cannot edit this menu")

        Company.validate_passcode(self, attrs, current_company_member)

        return attrs

    def create(self, validated_data):
        last_menu_category = MenuCategory.objects.filter(menu=validated_data['menu']).order_by('-order').first()
        order = last_menu_category.order+1 if last_menu_category else 0

        validated_data["order"] = order

        menu_category = super(MenuCategoryCreateSerializer, self).create(validated_data)

        return menu_category


class MenuCategoryDetailSerializer(ListModelSerializer):
    menu_items = serializers.SerializerMethodField()
    category = CategoryListSerializer()

    class Meta:
        model = MenuCategory
        fields = "__all__"

    def get_menu_items(self, instance):
        menu_items = instance.items.all()
        return MenuItemMenuListSerializer(menu_items, many=True).data
