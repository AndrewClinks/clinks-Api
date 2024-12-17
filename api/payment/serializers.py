from ..utils.Serializers import serializers, ValidateModelSerializer, CreateModelSerializer, ListModelSerializer

from ..currency.models import Currency
from ..card.models import Card
from ..company.models import Company
from ..customer.models import Customer

from ..currency.serializers import CurrencyDetailSerializer

from ..utils.stripe import Payment as StripePayment
from ..utils import DateUtils

from .models import Payment


class PaymentValidateSerializer(ValidateModelSerializer):
    card = serializers.IntegerField()
    payment_intent_id = serializers.CharField(required=False)
    expected_price = serializers.IntegerField(min_value=0)

    class Meta:
        model = Payment
        fields = ["card", "payment_intent_id", "expected_price", "tip"]


class PaymentCreateSerializer(CreateModelSerializer):
    card = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    payment_intent_id = serializers.CharField(required=False)
    expected_price = serializers.IntegerField(min_value=0)

    amount = serializers.IntegerField(min_value=0)
    tip = serializers.IntegerField(min_value=0, default=0)
    service_fee = serializers.IntegerField(min_value=0)
    delivery_fee = serializers.IntegerField(min_value=0)
    delivery_driver_fee = serializers.IntegerField(min_value=0, required=False)
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())

    class Meta:
        model = Payment
        fields = ["card", "payment_intent_id", "expected_price", "tip", "amount", "service_fee", "delivery_fee", "company",
                  "customer", "currency", "delivery_driver_fee"]

    def validate(self, attrs):
        customer = attrs["customer"]
        card = attrs["card"]
        amount = attrs["amount"]
        tip = attrs["tip"]
        service_fee = attrs["service_fee"]
        delivery_fee = attrs["delivery_fee"]
        expected_price = attrs.pop("expected_price")

        total_amount = round(amount + tip + service_fee + delivery_fee)

        if expected_price != total_amount:
            self.raise_validation_error("Payment", "The price of items on your basket has changed, please recreate your order")

        if card and card.customer != customer:
            self.raise_validation_error("Payment", "This card with this id does not exist")

        attrs = self.payment_validation(attrs)

        return attrs

    def payment_validation(self, attrs):
        payment_intent_id = attrs.pop("payment_intent_id") if "payment_intent_id" in attrs else None

        company = attrs["company"]
        card = attrs.get("card")
        currency = attrs.get("currency")

        amount = attrs["amount"]

        application_fee = round(attrs["tip"] + attrs["service_fee"] + attrs["delivery_fee"])

        total = amount + application_fee

        # If payment_intent_id is not provided (1st call from app), then call get_payment_intent
        # If payment_intent_id is provided (2nd call from app), then call create_payment_intent
        payment_intent = StripePayment.charge(
            self,
            payment_intent_id,
            lambda: StripePayment.create_payment_intent(
                total,
                currency,
                "Payment for order",
                card.stripe_payment_method_id,
                company.stripe_account_id,
                application_fee_amount=application_fee,
                stripe_customer_account_id=card.customer.stripe_customer_id
            ),
            lambda: StripePayment.get_payment_intent(
                payment_intent_id,
                company.stripe_account_id
            )
        )

        attrs.update(**StripePayment.get_payment_data(payment_intent, company.stripe_account_id))

        attrs["paid_at"] = DateUtils.now()

        return attrs


class PaymentOrderDetailSerializer(ListModelSerializer):
    currency = CurrencyDetailSerializer()

    class Meta:
        model = Payment
        fields = ["id", "currency", "total", "amount", "tip", "service_fee", "delivery_fee"]


class PaymentOrderDriverDetailSerializer(ListModelSerializer):
    currency = CurrencyDetailSerializer()
    potential_earning = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ["potential_earning", "currency"]

    def get_potential_earning(self, instance):
        return instance.delivery_driver_fee + instance.tip


class PaymentListSerializer(ListModelSerializer):
    from ..company.serializers import CompanyTitleSerializer
    from ..currency.serializers import CurrencyListSerializer

    company = CompanyTitleSerializer()
    currency = CurrencyListSerializer()
    order = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ["id", "company", "currency", "total", "delivery_fee", "tip", "amount", "service_fee", "paid_at",
                  "refunded_at",  "order", "created_at"]

    def get_order(self, instance):
        from ..order.serializers import OrderPaymentListSerializer
        order = instance.order
        return OrderPaymentListSerializer(order).data

    def get_select_related_fields(self):
        return ["order", "company", "currency"]