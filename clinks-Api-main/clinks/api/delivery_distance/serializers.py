from ..utils.Serializers import serializers, CreateSerializer, ValidateModelSerializer, ListSerializer, ListModelSerializer

from ..utils import Constants

from django.db.models import Q

from .models import DeliveryDistance

ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


class DeliveryDistanceValidateSerializer(ValidateModelSerializer):

    class Meta:
        model = DeliveryDistance
        fields = "__all__"

    def validate(self, attrs):
        starts = attrs["starts"]
        ends = attrs["ends"]
        driver_fee = attrs["driver_fee"]
        fee = attrs["fee"]

        if starts > ends:
            self.raise_validation_error("DeliveryDistance", "'starts' cannot be bigger than 'ends'")

        if starts == ends:
            self.raise_validation_error("DeliveryDistance", "'starts' cannot be equal to 'ends'")

        if driver_fee > fee:
            self.raise_validation_error("DeliveryDistance", "driver_fee cannot be bigger than fee")

        return attrs


class DeliveryDistanceBulkCreateSerializer(CreateSerializer):
    delivery_distances = DeliveryDistanceValidateSerializer(many=True, allow_null=False, allow_empty=False)

    def validate(self, attrs):
        delivery_distances = attrs["delivery_distances"]

        self.delivery_distances_range_validation(delivery_distances)

        return attrs

    def create(self, validated_data):
        delivery_distances_data = validated_data.pop("delivery_distances")

        DeliveryDistance.objects.delete()

        delivery_distances = []

        for delivery_distance_data in delivery_distances_data:
            delivery_distance = DeliveryDistance.objects.create(**delivery_distance_data)
            delivery_distances.append(delivery_distance)

        return delivery_distances

    def delivery_distances_range_validation(self, delivery_distances):
        delivery_distances_no = len(delivery_distances)
        if delivery_distances[0]["starts"] != 0.00:
            raise serializers.ValidationError("1st delivery distance should start from 0")

        for index in range(0, delivery_distances_no - 1):
            if delivery_distances[index]["ends"] != delivery_distances[index + 1]["starts"]:
                raise serializers.ValidationError(
                        f"{ordinal(index+1)} delivery distance's 'ends' must match {ordinal(index+2)} delivery distance's 'starts'")


class DeliveryDistanceListSerializer(ListModelSerializer):

    class Meta:
        model = DeliveryDistance
        fields = "__all__"


class DeliveryDistanceBulkDetailSerializer(ListSerializer):
    delivery_distances = serializers.SerializerMethodField()

    def get_delivery_distances(self, instance):
        data = DeliveryDistance.objects.order_by("starts")
        return DeliveryDistanceListSerializer(data, many=True).data