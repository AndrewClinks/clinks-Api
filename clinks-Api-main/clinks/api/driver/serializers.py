from ..utils.Serializers import serializers, CreateModelSerializer, EditModelSerializer, ListModelSerializer
from ..user.serializers import (UserDriverCreateSerializer,
                                UserDetailSerializer,
                                UserAdminEditSerializer,

                                )
from ..identification.serializers import (Identification,
                                          IdentificationCreateSerializer,
                                          IdentificationEditSerializer,
                                          IdentificationListSerializer)

from ..all_time_stat.models import AllTimeStat

from ..utils import Constants, DateUtils

from .models import Driver
from ..setting.models import Setting

import logging
logger = logging.getLogger('clinks-api-live')

class DriverCreateSerializer(CreateModelSerializer):

    user = UserDriverCreateSerializer()
    identification = IdentificationCreateSerializer(required=False, allow_null=True)
    vehicle_type = serializers.CharField()

    class Meta:
        model = Driver
        fields = ["user", "identification", "ppsn", "vehicle_type", "vehicle_registration_no"]

    def validate_vehicle_type(self, vehicle_type):
        return self.validate_enum_field("Vehicle Type", vehicle_type, Constants.VEHICLE_TYPES)

    def validate(self, attrs):
        user_data = attrs['user']
        user_data["role"] = Constants.USER_ROLE_DRIVER

        check_required_documents(self, attrs)
        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        identification_data = validated_data.pop("identification", None)

        serializer = UserDriverCreateSerializer(data=user_data)
        user = serializer.create(user_data)
        validated_data["user"] = user

        if identification_data:
            serializer = IdentificationCreateSerializer(data=identification_data)
            identification = serializer.create(identification_data)
            validated_data["identification"] = identification

        driver = Driver.objects.create(**validated_data)

        AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_DRIVER_COUNT, Driver.objects.count(), True)

        return driver


class DriverAdminEditSerializer(EditModelSerializer):

    user = UserAdminEditSerializer(partial=True)
    identification = IdentificationEditSerializer(required=False, allow_null=True)
    vehicle_type = serializers.CharField()

    class Meta:
        model = Driver
        fields = ["user", "identification", "ppsn", "vehicle_type", "vehicle_registration_no"]

    def validate_vehicle_type(self, vehicle_type):
        return self.validate_enum_field("Vehicle Type", vehicle_type, Constants.VEHICLE_TYPES)

    def validate(self, attrs):
        check_required_documents(self, attrs, self.instance)
        return attrs

    def update(self, instance, validated_data):

        user_data = validated_data.pop("user", None)
        identification_data = validated_data.get("identification", None)

        if user_data:
            serializer = UserAdminEditSerializer(instance=instance.user, data=user_data, partial=True)
            serializer.update(instance.user, user_data)

        if "identification" in validated_data:
            validated_data["identification"] = save_identification(instance, identification_data)

        return super(DriverAdminEditSerializer, self).update(instance, validated_data)


class DriverEditSerializer(EditModelSerializer):
    latitude = serializers.FloatField(allow_null=True)
    longitude = serializers.FloatField(allow_null=True)

    class Meta:
        model = Driver
        fields = ["latitude", "longitude"]

    def validate(self, attrs):
        latitude = attrs.get("latitude", None)
        longitude = attrs.get("longitude", None)
        if (latitude and not longitude) or (not latitude and longitude):
            self.raise_validation_error("Driver", "'latitude' or 'longitude' is null when one of them is provided")

        return attrs

    def update(self, instance, validated_data):
        from django.contrib.gis.geos import Point
        # Not sure what this is doing
        reset_last_known_location = "latitude" in validated_data and "longitude" in validated_data and not validated_data["latitude"] and not validated_data["longitude"]
        longitude = validated_data.pop('longitude', None)
        latitude = validated_data.pop('latitude', None)

        if latitude and longitude:
            point = Point(longitude, latitude)
            validated_data['last_known_location'] = point

        if reset_last_known_location:
            validated_data["last_known_location"] = None

        if "last_known_location" in validated_data:
            instance.last_known_location = validated_data["last_known_location"]
            instance.last_known_location_updated_at = DateUtils.now()
            # Logging the driver's ID and location updates
            logger.info(
                f"Driver ID: {instance.user.id} - Updating last_known_location "
                f"to Lat:{latitude} Long:{longitude} Point: {point}"
            )
            logger.info(
                f"Driver ID: {instance.user.id} - last_known_location_updated_at: {instance.last_known_location_updated_at}"
            )
            instance.save(update_fields=["last_known_location", "last_known_location_updated_at"])

        return instance


def save_identification(instance, data):
    if not data:
        identification = instance.identification
        if identification:
            identification.delete()

        return None

    if "id" in data:
        serializer = IdentificationEditSerializer(instance=instance.identification, data=data)
        identification = serializer.update(instance.identification, data)
        return identification

    serializer = IdentificationCreateSerializer(data=data)
    identification = serializer.create(data)

    return identification


class DriverListSerializer(ListModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    user = UserDetailSerializer()
    identification = IdentificationListSerializer()
    current_delivery_request = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = ["user", "identification", "vehicle_type", "vehicle_registration_no", "order_count",  "ppsn",
                  "last_known_location", "last_known_location_updated_at", "current_delivery_request", "latitude",
                  "longitude"]

    def get_select_related_fields(self):
        return ["user", "identification"]

    def get_latitude(self, instance):
        if not instance.last_known_location:
            return None
        return instance.last_known_location.coords[1]

    def get_longitude(self, instance):
        if not instance.last_known_location:
            return None
        return instance.last_known_location.coords[0]

    def get_current_delivery_request(self, instance):
        if not instance.current_delivery_request:
            return None
        return instance.current_delivery_request.id


class DriverAdminDetailSerializer(DriverListSerializer):

    class Meta(DriverListSerializer.Meta):
        fields = DriverListSerializer.Meta.fields + ["total_earnings", "average_delivery_time"]


class DriverDetailSerializer(DriverListSerializer):
    class Meta(DriverListSerializer.Meta):
        fields = DriverListSerializer.Meta.fields + ["total_earnings", "order_count"]

    def get_current_delivery_request(self, instance):
        from ..delivery_request.serializers import DeliveryRequestDriverDetailSerializer
        current_delivery_request = instance.current_delivery_request

        if not current_delivery_request:
            return None

        return DeliveryRequestDriverDetailSerializer(current_delivery_request).data


class DriverOrderDetailSerializer(ListModelSerializer):
    user = UserDetailSerializer()

    class Meta:
        model = Driver
        fields = ["user"]


def check_required_documents(serializer, attrs, instance=None):
    vehicle_type = attrs["vehicle_type"] if "vehicle_type" in attrs else instance.vehicle_type
    identification = attrs.get("identification", None)
    vehicle_registration_no = attrs.get("vehicle_registration_no", None)

    if instance:
        vehicle_registration_no = vehicle_registration_no if "vehicle_registration_no" in attrs else instance.vehicle_registration_no
        identification = identification if "identification" in attrs else instance.identification

    if vehicle_type != Constants.VEHICLE_TYPE_BICYCLE:
        if not identification:
            serializer.raise_validation_error("Driver", "'identification' is required")
        if not vehicle_registration_no:
            serializer.raise_validation_error("Driver", "'vehicle_registration_no' is required")

    if identification:
        identification_type = identification.type if type(identification) == Identification else identification.get("type")
        identification_id = identification.id if type(identification) == Identification else identification.get("id")
        if identification_type != Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE:
            serializer.raise_validation_error("Driver", f"Identification type has to be {Constants.IDENTIFICATION_TYPE_DRIVER_LICENSE}")

        if identification_id and Driver.objects.filter(identification_id=identification_id).exclude(user_id=instance.user_id).exists():
            serializer.raise_validation_error("Driver", "This identification is used by different driver")

    return attrs
