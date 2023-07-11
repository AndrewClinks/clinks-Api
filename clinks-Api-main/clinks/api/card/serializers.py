from ..utils.Serializers import serializers, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from ..utils.stripe import Customer

from .models import Card


class CardCreateSerializer(CreateModelSerializer):
    source = serializers.CharField()
    default = serializers.BooleanField()

    class Meta:
        model = Card
        fields = ["customer", "source", "default", ]

    def create(self, validated_data):
        customer = validated_data["customer"]
        source = validated_data["source"]
        default = validated_data["default"]

        try:
            card = Customer.add_card(customer, source, default)
        except Exception as error:
            self.raise_validation_error("card", error.detail)

        if card.default:
            Card.objects.filter(customer=card.customer).exclude(id=card.id).update(default=False)

        return card


class CardEditSerializer(EditModelSerializer):
    default = serializers.BooleanField()

    class Meta:
        model = Card
        fields = ["default"]

    def update(self, instance, validated_data):
        default = validated_data["default"]

        if not default:
            return instance

        Card.objects.filter(customer=instance.customer).exclude(id=instance.id).update(default=False)

        instance.default = True
        instance.save()

        return instance


class CardListSerializer(ListModelSerializer):

    class Meta:
        model = Card
        exclude = ["stripe_payment_method_id", ]


class CardDetailSerializer(CardListSerializer):
    pass


