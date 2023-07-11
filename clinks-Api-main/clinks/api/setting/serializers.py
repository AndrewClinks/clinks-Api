from ..utils.Serializers import serializers, ValidateModelSerializer, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from .models import Setting

from ..utils import Constants


class SettingCreateSerializer(CreateModelSerializer):
    key = serializers.CharField()

    class Meta:
        model = Setting
        fields = "__all__"

    def validate_key(self, key):
        return self.validate_enum_field("Key", key.lower(), Constants.SETTING_KEYS)

    def validate(self, attrs):
        key = attrs["key"].lower()
        value = attrs["value"]

        self.check_value_type(key, value)

        if key == Constants.SETTING_KEY_MINIMUM_AGE and int(value) < 18:
            self.raise_validation_error("Setting", "Minimum age cannot be less than 18")

        if key == Constants.SETTING_KEY_MINIMUM_ORDER_AMOUNT and int(value) < 50:
            self.raise_validation_error("Setting", "Minimum order amount cannot be less than 50 cents")

        return attrs

    def create(self, validated_data):
        key = validated_data["key"]
        value = validated_data["value"]

        setting = Setting.update(key, value)

        return setting

    def check_value_type(self, key, value):
        if key in Constants.SETTING_KEYS_INTEGER:
            try:
                int(value)
            except Exception as e:
                self.raise_validation_error("Setting", "value has to be an integer")

        return


class SettingListSerializer(ListModelSerializer):

    class Meta:
        model = Setting
        fields = "__all__"


class SettingDetailSerializer(SettingListSerializer):
    pass






