from ..utils.Serializers import (serializers, CreateModelSerializer, ListModelSerializer, EditModelSerializer)

from django.contrib.gis.geos import Point

from .models import Address


class AddressCreateSerializer(CreateModelSerializer):
    latitude = serializers.FloatField(required=True, write_only=True)
    longitude = serializers.FloatField(required=True, write_only=True)

    class Meta:
        model = Address
        exclude = ["point"]

    def create(self, validated_data):
        longitude = validated_data.pop('longitude')
        latitude = validated_data.pop('latitude')

        point = Point(longitude, latitude)

        validated_data['point'] = point
        return Address.objects.create(**validated_data)


class AddressEditSerializer(EditModelSerializer):
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)

    class Meta:
        model = Address
        exclude = ["point"]

    def update(self, instance, validated_data):
        longitude = validated_data.pop('longitude', None)
        latitude = validated_data.pop('latitude', None)

        if longitude is not None and latitude is not None:
            point = Point(longitude, latitude)
            instance.point = point

        address = super(AddressEditSerializer, self).update(instance, validated_data)

        return address


class AddressListSerializer(ListModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Address
        exclude = ('updated_at', 'created_at', 'point')

    def get_latitude(self, instance):
        return instance.point.coords[1]

    def get_longitude(self, instance):
        return instance.point.coords[0]


class AddressDetailSerializer(AddressListSerializer):
    pass

