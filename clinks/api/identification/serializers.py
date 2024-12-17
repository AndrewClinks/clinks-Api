from rest_framework import serializers

from .models import Identification

from ..utils.Serializers import CreateModelSerializer, EditModelSerializer, ListModelSerializer

from ..image.serializers import ImageListSerializer

from ..image.models import Image

from django.db.models import Q

from ..utils import Constants


class IdentificationCreateSerializer(CreateModelSerializer):
    type = serializers.CharField()

    class Meta:
        model = Identification
        fields = "__all__"

    def validate_type(self, type):
        return self.validate_enum_field("type", type, Constants.IDENTIFICATION_TYPES)

    def validate(self, attrs):
        type = attrs["type"]
        back = attrs.get("back", None)

        if type != Constants.IDENTIFICATION_TYPE_PASSPORT and not back:
            self.raise_validation_error("Identification", "You have to upload back of this identification")

        return attrs


class IdentificationEditSerializer(EditModelSerializer):
    id = serializers.IntegerField(required=False)
    type = serializers.CharField()
    front = serializers.IntegerField(required=False)
    back = serializers.IntegerField(required=False)

    class Meta:
        model = Identification
        fields = "__all__"

    def validate_type(self, type):
        return self.validate_enum_field("type", type, Constants.IDENTIFICATION_TYPES)

    def validate_front(self, front):
        return Image.objects.get(id=front)

    def validate_back(self, back):
        return Image.objects.get(id=back)

    def validate(self, attrs):
        type = attrs["type"] if "type" in attrs else self.instance.type
        back = attrs["back"] if "back" in attrs else self.instance.back
        front = attrs["front"] if "front" in attrs else self.instance.front

        if type != Constants.IDENTIFICATION_TYPE_PASSPORT and not back:
            self.raise_validation_error("Identification", "You have to upload back of this identification")

        if "id" not in attrs and Identification.objects.filter(Q(front_id=front.id)|Q(back_id=back.id)).exists():
            self.raise_validation_error("Identification", "front and back needs to be unique")

        return attrs


class IdentificationListSerializer(ListModelSerializer):
    front = ImageListSerializer()
    back = ImageListSerializer()

    class Meta:
        model = Identification
        fields = "__all__"


class IdentificationDetailSerializer(IdentificationListSerializer):
    pass
