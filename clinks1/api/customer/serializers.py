from ..utils.Serializers import CreateModelSerializer, EditModelSerializer, ListModelSerializer
from ..user.serializers import (UserCustomerCreateSerializer,
                                UserEditSerializer,
                                UserDetailSerializer,
                                UserCustomerEditSerializer
                                )
from ..identification.serializers import (IdentificationCreateSerializer, IdentificationEditSerializer)
from ..address.serializers import Address, AddressCreateSerializer, AddressDetailSerializer

from ..identification.models import Identification

from ..all_time_stat.models import AllTimeStat
from ..utils import Constants, DateUtils

from .models import Customer
from ..setting.models import Setting


class CustomerCreateSerializer(CreateModelSerializer):

    user = UserCustomerCreateSerializer()

    class Meta:
        model = Customer
        fields = ["user",]

    def validate(self, attrs):
        user_data = attrs['user']
        user_data["role"] = Constants.USER_ROLE_CUSTOMER

        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop("user")

        serializer = UserCustomerCreateSerializer(data=user_data)
        user = serializer.create(user_data)
        validated_data["user"] = user

        customer = Customer.objects.create(**validated_data)

        AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_CUSTOMER_COUNT, 1)

        return customer


class CustomerEditSerializer(EditModelSerializer):

    user = UserCustomerEditSerializer(partial=True)
    address = AddressCreateSerializer(required=False)
    identification = IdentificationCreateSerializer(required=False)

    class Meta:
        model = Customer
        fields = ["user", "address", "identification"]

    def validate(self, attrs):
        identification_validation(self, attrs, self.instance)
        return attrs

    def update(self, instance, validated_data):
        address_data = validated_data.pop("address", None)
        user_data = validated_data.pop("user", None)
        identification_data = validated_data.pop("identification", None)

        if user_data:
            serializer = UserCustomerEditSerializer(instance=instance.user, data=user_data, partial=True)
            serializer.update(instance.user, user_data)

        if address_data:
            Address.create_or_update_for(self.instance, address_data)

        if identification_data:
            identification = save_identification(identification_data)
            validated_data["identification"] = identification

        return super(CustomerEditSerializer, self).update(instance, validated_data)


class CustomerListSerializer(ListModelSerializer):

    user = UserDetailSerializer()

    class Meta:
        model = Customer
        fields = ["user", "order_count", "last_order_at"]

    def get_select_related_fields(self):
        return ["user", ]


class CustomerDetailSerializer(CustomerListSerializer):
    address = AddressDetailSerializer()

    class Meta(CustomerListSerializer.Meta):
        fields = CustomerListSerializer.Meta.fields + ["total_spending", "average_spending_per_order", "address"]


class CustomerOrderDetailSerializer(ListModelSerializer):
    user = UserDetailSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ["user"]


def identification_validation(serializer, attrs, instance=None):
    identification = attrs.get("identification", None)
    date_of_birth = attrs["user"]["date_of_birth"] if "user" in attrs and "date_of_birth" in attrs["user"] \
        else instance.user.date_of_birth

    if not identification:
        return attrs

    identification_id = identification.id if type(identification) == Identification else identification.get(
        "id")

    if identification_id and Customer.objects.filter(identification_id=identification_id).exclude(
            user_id=instance.user_id).exists():
        serializer.raise_validation_error("Customer", "This identification is used by different customer")

    return attrs


def save_identification(data, instance=None):
    if not data:
        instance.identification.delete()
        return None

    if "id" in data:
        serializer = IdentificationEditSerializer(instance=instance.identification, data=data)
        identification = serializer.update(instance.identification, data)
        return identification

    serializer = IdentificationCreateSerializer(data=data)
    identification = serializer.create(data)

    return identification
