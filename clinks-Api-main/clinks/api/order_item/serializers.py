from ..utils.Serializers import serializers, ValidateSerializer, ListSerializer

from ..item.serializers import ItemAdminDetailSerializer
from ..currency.serializers import CurrencyDetailSerializer
from ..menu_item.serializers import MenuItem, MenuOrderDetailSerializer


class OrderItemValidateSerializer(ValidateSerializer):
    id = serializers.IntegerField()

    quantity = serializers.IntegerField(min_value=1)

    price = serializers.IntegerField(read_only=True)
    price_sale = serializers.IntegerField(read_only=True)

    def validate(self, attrs):
        id_ = attrs["id"]
        menu_item = MenuItem.objects.filter(id=id_).first()
        if not menu_item:
            self.raise_validation_error("OrderItem", "Menu item does not exist")

        attrs.update({
            "price": menu_item.price,
            "price_sale": menu_item.price_sale
        })
        return attrs


class OrderItemDetailSerializer(ListSerializer):
    id = serializers.IntegerField()
    quantity = serializers.IntegerField()

    item = ItemAdminDetailSerializer(required=False, read_only=True)
    price = serializers.IntegerField(read_only=True)
    price_sale = serializers.IntegerField(read_only=True)
    currency = CurrencyDetailSerializer(read_only=True)

    def to_representation(self, instance):
        id_ = instance["id"]
        menu_item = MenuItem.objects.get(id=id_)
        instance.update(MenuOrderDetailSerializer(menu_item).data)

        return instance

    # def validate(self, attrs):
    #     id_ = attrs["id"]
    #     menu_item = MenuItem.objects.get(id=id_)
    #     attrs.update(MenuItemMenuListSerializer(menu_item).data)
    #     return attrs


