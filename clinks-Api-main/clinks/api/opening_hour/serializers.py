from ..utils.Serializers import serializers, ValidateModelSerializer, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from .models import OpeningHour

from ..utils import Constants


class OpeningHourValidateSerializer(ValidateModelSerializer):
    id = serializers.IntegerField(required=False)
    day = serializers.CharField()

    class Meta:
        model = OpeningHour
        exclude = ["venue", "order"]

    def validate(self, attrs):
        return validation(self, attrs)


class OpeningHourCreateSerializer(CreateModelSerializer):

    class Meta:
        model = OpeningHour
        fields = "__all__"

    def validate(self, attrs):
        return validation(self, attrs)


class OpeningHourEditSerializer(EditModelSerializer):
    class Meta:
        model = OpeningHour
        exclude = ["venue"]

    def validate(self, attrs):
        return validation(self, attrs)


class OpeningHourListSerializer(ListModelSerializer):

    class Meta:
        model = OpeningHour
        exclude = ["venue"]


class OpeningHourDetailSerializer(OpeningHourListSerializer):
    pass


def validation(serializer, attrs):
    day = attrs["day"] if "day" in attrs else None

    starts_at = attrs["starts_at"] if "starts_at" in attrs else None
    ends_at = attrs["ends_at"] if "ends_at" in attrs else None

    # if day is None or starts_at is None or ends_at is None:
    #     serializer.raise_validation_error("Hour", "'day', 'start_at' and 'ends_at' are required")

    if day not in Constants.DAYS:
        serializer.raise_validation_error("Day", f"'day' needs to be one of {Constants.DAYS_ORDERED}")

    if starts_at > ends_at:
        serializer.raise_validation_error("Time", "'starts_at' cannot be later than 'ends_at'")

    if starts_at == ends_at:
        serializer.raise_validation_error("Time", "'starts_at' and 'ends_at' cannot be same")

    return attrs
