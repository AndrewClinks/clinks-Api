from ..utils.Serializers import serializers, CreateModelSerializer, EditModelSerializer, ListModelSerializer
from ..user.serializers import (UserCreateSerializer,
                                UserEditSerializer,
                                UserAdminEditSerializer,
                                UserDetailSerializer,
                                )

from ..utils import Constants

from .models import Admin


class AdminCreateSerializer(CreateModelSerializer):

    user = UserCreateSerializer()

    class Meta:
        model = Admin
        fields = ["user", ]

    def validate(self, attrs):
        user_data = attrs['user']

        user_data["role"] = Constants.USER_ROLE_ADMIN
        attrs["role"] = Constants.ADMIN_ROLE_STAFF

        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop("user")

        serializer = UserCreateSerializer(data=user_data)
        user = serializer.create(user_data)
        validated_data["user"] = user

        client = super(AdminCreateSerializer, self).create(validated_data)

        return client


class AdminEditSerializer(EditModelSerializer):
    user = UserEditSerializer(partial=True)

    class Meta:
        model = Admin
        fields = ["user", ]

    def update(self, instance, validated_data):
        if 'user' in validated_data:
            user_data = validated_data.pop("user")
            serializer = self.get_user_edit_serializer()(instance=instance.user, data=user_data, partial=True)
            serializer.update(instance.user, user_data)

        return super(AdminEditSerializer, self).update(instance, validated_data)

    def get_user_edit_serializer(self):
        return UserEditSerializer


class AdminSuperEditSerializer(AdminEditSerializer):
    user = UserAdminEditSerializer(partial=True)

    def get_user_edit_serializer(self):
        return UserAdminEditSerializer


class AdminListSerializer(ListModelSerializer):

    user = UserDetailSerializer()

    class Meta:
        model = Admin
        fields = ["user", "role"]

    def get_select_related_fields(self):
        return ["user", ]


class AdminDetailSerializer(AdminListSerializer):
    pass
