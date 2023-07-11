from ..utils.Serializers import serializers, ValidateModelSerializer, CreateModelSerializer, ListModelSerializer

from ..currency.serializers import CurrencyListSerializer
from ..driver.serializers import DriverOrderDetailSerializer

from .models import DriverPayment


class DriverPaymentListSerializer(ListModelSerializer):
    driver = DriverOrderDetailSerializer()
    currency = CurrencyListSerializer()

    class Meta:
        model = DriverPayment
        fields = ["id", "driver", "order", "currency", "amount", "type", "created_at"]

    def get_select_related_fields(self):
        return ["driver", "currency"]
