from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password

from .models import User

from ..utils import Constants, DateUtils

from ..utils.Serializers import (
    CreateModelSerializer,
    EditModelSerializer,
    ListModelSerializer,
)


from django.core import exceptions
import django.contrib.auth.password_validation as validators


class UserCreateSerializer(CreateModelSerializer):

    class Meta:
        model = User
        fields = '__all__'

    def validate_role(self, role):
        if role not in Constants.USER_ROLES:
            error = "role must be one of {}".format(Constants.USER_ROLES)
            raise serializers.ValidationError(error)

        return role

    def validate_status(self, status):
        if status not in Constants.USER_STATUSES:
            error = "status must be one of {}".format(Constants.USER_STATUSES)
            raise serializers.ValidationError(error)

        return status

    def validate_email(self, email):
        if User.objects.filter(email__iexact=email).exists():
            error = "A user with this email already exists"
            raise serializers.ValidationError(error)

        return email

    def validate_password(self, password):
        return password_validate(password)

    def validate(self, attrs):
        phone_number = attrs.get("phone_number", None)
        phone_country_code = attrs.get("phone_country_code", None)

        if (phone_country_code is not None and phone_number is None) or (phone_country_code is None and phone_number is not None):
            self.raise_validation_error("User", "'phone_number' or 'phone_country_code' cannot be null if one of them is provided")

        return attrs

    def get_mandatory_fields(self):
        return []


class UserCustomerCreateSerializer(UserCreateSerializer):
    date_of_birth = serializers.DateField(required=True)

    def validate_date_of_birth(self, date_of_birth):
        if DateUtils.year_difference_to_now(date_of_birth) < 18:
            raise serializers.ValidationError("You need to be at least 18 years old to use this app.")

        return date_of_birth


class UserDriverCreateSerializer(UserCreateSerializer):
    phone_number = serializers.CharField(required=True)
    phone_country_code = serializers.CharField(required=True)


class UserCompanyMemberCreateSerializer(UserCreateSerializer):
    phone_number = serializers.CharField(required=True)
    phone_country_code = serializers.CharField(required=True)


class UserBasicDetailSerializer(ListModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", 'phone_country_code', 'phone_number',]


class UserEditSerializer(EditModelSerializer):

    current_password = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'password',
            'current_password',
            'phone_country_code',
            'phone_number',
        ]

    def validate_password(self, password):
        return password_validate(password)

    def validate(self, attrs):
        phone_number = attrs.get("phone_number", None)
        phone_country_code = attrs.get("phone_country_code", None)

        if (phone_country_code is not None and phone_number is None) or (phone_country_code is None and phone_number is not None):
            self.raise_validation_error("User", "'phone_number' or 'phone_country_code' cannot be null")

        return attrs

    def update(self, instance, validated_data):
        if 'password' in validated_data and 'current_password' not in validated_data:
            raise serializers.ValidationError("Please include current_password in order to update your password")

        if 'password' in validated_data:
            current_password = validated_data.pop("current_password")
            if not check_password(current_password, instance.password):
                raise serializers.ValidationError("Invalid request, your old password is incorrect")

        return super(UserEditSerializer, self).update(instance, validated_data)


class UserCustomerEditSerializer(EditModelSerializer):
    email = serializers.EmailField(required=False)
    current_password = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'password',
            'current_password',
            'phone_country_code',
            'phone_number',
            'email'
        ]

    def validate_email(self, email):
        if self.parent and self.parent.instance and self.parent.instance.user.email == email:
            return email

        if User.objects.filter(email__iexact=email).exists():
            error = "A user with this email already exists"
            raise serializers.ValidationError(error)

        return email

    def validate_password(self, password):
        return password_validate(password)

    def validate(self, attrs):
        phone_number = attrs.get("phone_number", None)
        phone_country_code = attrs.get("phone_country_code", None)

        if (phone_country_code is not None and phone_number is None) or (
                phone_country_code is None and phone_number is not None):
            self.raise_validation_error("User", "'phone_number' or 'phone_country_code' cannot be null if one of them is provided")

        if 'password' in attrs and 'current_password' not in attrs:
            raise serializers.ValidationError("Please include current_password in order to update your password")

        if 'email' in attrs and 'current_password' not in attrs:
            raise serializers.ValidationError("Please include current_password in order to update your email")

        return attrs

    def update(self, instance, validated_data):
        if 'password' in validated_data or "email" in validated_data:
            current_password = validated_data.pop("current_password")
            if not check_password(current_password, instance.password):
                message = "Invalid request, your old password is incorrect" if 'password' in validated_data else "Your current password is incorrect"
                raise serializers.ValidationError(message)

        return super(UserCustomerEditSerializer, self).update(instance, validated_data)


class UserAdminEditSerializer(UserEditSerializer):
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = UserEditSerializer.Meta.fields + ['status', 'email']

    def validate_email(self, email):
        if self.parent and self.parent.instance and self.parent.instance.user.email == email:
            return email

        if User.objects.filter(email__iexact=email).exists():
            error = "A user with this email already exists"
            raise serializers.ValidationError(error)

        return email

    def validate(self, attrs):
        phone_number = attrs.get("phone_number", None)
        phone_country_code = attrs.get("phone_country_code", None)

        if (phone_country_code is not None and phone_number is None) or (
                phone_country_code is None and phone_number is not None):
            self.raise_validation_error("User", "'phone_number' or 'phone_country_code' cannot be null if one of them is provided")

        return attrs

    def update(self, instance, validated_data):
        return super(UserEditSerializer, self).update(instance, validated_data)


class UserDriverAdminEditSerializer(UserAdminEditSerializer):
    phone_number = serializers.CharField(allow_null=False)
    phone_country_code = serializers.CharField(allow_null=False)


class UserCompanyMemberEditSerializer(UserEditSerializer):
    phone_number = serializers.CharField(allow_null=False)
    phone_country_code = serializers.CharField(allow_null=False)


class UserCompanyMemberAdminEditSerializer(UserCompanyMemberEditSerializer, UserAdminEditSerializer):
    pass


class UserListSerializer(ListModelSerializer):

    class Meta:
        model = User
        exclude = ['password', 'verification_code', 'status', 'active', 'email_verified', 'last_seen',
                   'updated_at']


class UserDetailSerializer(UserListSerializer):

    class Meta:
        model = User
        exclude = ['password', 'verification_code', 'status', 'active', 'last_seen', 'updated_at']


class UserAdminListSerializer(ListModelSerializer):

    class Meta:
        model = User
        exclude = ['password']


class UserAdminDetailSerializer(UserAdminListSerializer):
    pass


def password_validate(password, raise_error_with_serializer=True):
    try:
        validators.validate_password(password=password, user=User)

    except exceptions.ValidationError as e:
        error = e.messages[0]

        if raise_error_with_serializer:
            raise serializers.ValidationError(error)
        else:
            raise Exception(error)

    return make_password(password)



