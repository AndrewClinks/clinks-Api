from ..utils.Serializers import serializers, ValidateModelSerializer, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from ..currency.serializers import CurrencyDetailSerializer

from ..item.serializers import ItemMenuListSerializer, ItemOrderDetailSerializer
from ..venue.serializers import VenueCustomerListSerializer, VenueCustomerDistanceListSerializer
from ..company_member.models import CompanyMember, Company
from ..utils import Constants
from ..menu.models import Menu
from .models import MenuItem


class MenuItemCreateSerializer(CreateModelSerializer):
    menu = serializers.PrimaryKeyRelatedField(queryset=Menu.objects.all())
    current_company_member = serializers.PrimaryKeyRelatedField(queryset=CompanyMember.objects.all(), required=False)
    passcode = serializers.IntegerField(required=False)

    class Meta:
        model = MenuItem
        exclude = ["sales_count", "order"]

    def validate(self, attrs):
        menu_category = attrs["menu_category"]
        item = attrs["item"]
        price_sale = attrs["price_sale"]
        price = attrs["price"]
        menu = attrs["menu"]
        current_company_member = attrs.pop("current_company_member", None)

        if item.subcategory.parent != menu_category.category:
            self.raise_validation_error("MenuItem", "This item does not  belong to this category")

        if price_sale and price_sale >= price:
            self.raise_validation_error("MenuItem", "price_sale cannot be bigger than price")

        if menu_category.menu != menu:
            self.raise_validation_error("MenuItem", "This menu_category does not belong to this menu")

        if current_company_member and current_company_member.company != menu.venue.company:
            self.raise_validation_error("MenuItem", "You cannot edit this menu")

        Company.validate_passcode(self, attrs, current_company_member)

        return attrs

    def create(self, validated_data):
        menu = validated_data["menu"]
        currency = validated_data["currency"]
        menu_category = validated_data["menu_category"]
        last_menu_item = MenuItem.objects.filter(menu_category=menu_category).order_by('-order').first()
        order = last_menu_item.order+1 if last_menu_item else 0

        validated_data["order"] = order

        menu_item = super(MenuItemCreateSerializer, self).create(validated_data)

        MenuItem.update_menu_item_count_for(menu_item.item)

        company = menu_item.menu.venue.company
        if company.has_added_menu_items is False:
            company.has_added_menu_items = True

            if company.status == Constants.COMPANY_STATUS_SETUP_NOT_COMPLETED:
                company.status = Constants.COMPANY_STATUS_ACTIVE

            company.save()

        if menu.venue.currency is None:
            menu.venue.currency = currency
            menu.venue.save()

        return menu_item


class MenuItemEditSerializer(EditModelSerializer):

    class Meta:
        model = MenuItem
        exclude = ["order", "sales_count", "menu_category", "menu"]

    def validate(self, attrs):
        menu_category = attrs["menu_category"] if "menu_category" in attrs else self.instance.menu_category
        item = attrs["item"] if "item" in attrs else self.instance.item
        price = attrs["price"] if "price" in attrs else self.instance.price
        price_sale = attrs["price_sale"] if "price_sale" in attrs else self.instance.price_sale

        if item.subcategory.parent != menu_category.category:
            self.raise_validation_error("MenuItem", "This item does not belong to this category")

        if price_sale and price_sale >= price:
            error = "price cannot be less than price_sale" if "price" in attrs else "price_sale cannot be bigger than price"
            self.raise_validation_error("MenuItem", error)

        return attrs

    def update(self, instance, validated_data):
        menu_item = super(MenuItemEditSerializer, self).update(instance, validated_data)

        MenuItem.update_menu_item_count_for(menu_item.item)

        return menu_item


class MenuItemMenuListSerializer(ListModelSerializer):
    item = ItemMenuListSerializer()

    class Meta:
        model = MenuItem
        exclude = ["sales_count"]

    def get_select_related_fields(self):
        return ["item"]


class MenuItemListSerializer(MenuItemMenuListSerializer):
    venue = serializers.SerializerMethodField()
    currency = CurrencyDetailSerializer()

    def get_venue(self, instance):
        venue = instance.menu_category.menu.venue
        return VenueCustomerListSerializer(venue).data


class MenuItemCustomerListSerializer(MenuItemListSerializer):

    def get_venue(self, instance):
        venue = instance.menu_category.menu.venue
        venue.distance = instance.distance if hasattr(instance, "distance") else None
        return VenueCustomerDistanceListSerializer(venue).data


class MenuItemLowestPriceSerializer(ListModelSerializer):
    currency = CurrencyDetailSerializer()
    price = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ["price", "currency"]

    def get_price(self, instance):
        price = instance.price
        price_sale = instance.price_sale if instance.price_sale is not None else price
        return min(price, price_sale)


class MenuItemDetailSerializer(MenuItemMenuListSerializer):
    pass


class MenuOrderDetailSerializer(ListModelSerializer):
    item = ItemOrderDetailSerializer()

    class Meta:
        model = MenuItem
        exclude = ["sales_count"]

    def get_select_related_fields(self):
        return ["item"]