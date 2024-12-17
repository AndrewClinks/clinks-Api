from ..utils.Serializers import serializers, ValidateModelSerializer, CreateModelSerializer, EditModelSerializer, ListModelSerializer
from ..user.serializers import (UserCompanyMemberCreateSerializer,
                                UserCompanyMemberEditSerializer,
                                UserCompanyMemberAdminEditSerializer,
                                UserDetailSerializer,
                                UserBasicDetailSerializer
                                )

from ..utils import Constants

from .models import CompanyMember


class CompanyMemberValidateSerializer(ValidateModelSerializer):
    user = UserCompanyMemberCreateSerializer()

    class Meta:
        model = CompanyMember
        fields = ["user", ]

    def validate(self, attrs):
        user_data = attrs['user']
        user_data["role"] = Constants.USER_ROLE_COMPANY_MEMBER
        attrs["role"] = Constants.COMPANY_MEMBER_ROLE_STAFF
        return attrs


class CompanyMemberCreateSerializer(CreateModelSerializer):
    from ..venue.models import Venue
    venue = serializers.PrimaryKeyRelatedField(queryset=Venue.objects, required=False)
    user = UserCompanyMemberCreateSerializer()

    class Meta:
        model = CompanyMember
        fields = ["user", "company", "venue"]

    def validate(self, attrs):
        user_data = attrs['user']
        user_data["role"] = Constants.USER_ROLE_COMPANY_MEMBER
        attrs["role"] = Constants.COMPANY_MEMBER_ROLE_STAFF
        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        venue = validated_data.pop("venue", None)

        serializer = UserCompanyMemberCreateSerializer(data=user_data)
        user = serializer.create(user_data)
        validated_data["user"] = user

        company_member = super(CompanyMemberCreateSerializer, self).create(validated_data)

        if venue:
            from ..staff.serializers import StaffCreateSerializer
            data = {
                "company_member": company_member,
                "venue": venue.id
            }
            serializer = StaffCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.create(serializer.validated_data)

        return company_member


class CompanyMemberEditSerializer(EditModelSerializer):
    user = UserCompanyMemberEditSerializer(partial=True)

    class Meta:
        model = CompanyMember
        fields = ["user", "active_venue"]

    def validate(self, attrs):
        active_venue = attrs.get("active_venue", None)

        if active_venue and active_venue.company != self.instance.company:
            self.raise_validation_error("CompanyMember", "This venue does not belong to your company.")

        if active_venue and not active_venue.staff.filter(company_member__user_id=self.instance.user_id).exists():
            self.raise_validation_error("CompanyMember", "You aren't in staff list for this venue.")

        return attrs

    def update(self, instance, validated_data):
        if 'user' in validated_data:
            user_data = validated_data.pop("user")
            serializer = self.get_user_edit_serializer()(instance=instance.user, data=user_data, partial=True)
            serializer.update(instance.user, user_data)

        return super(CompanyMemberEditSerializer, self).update(instance, validated_data)

    def get_user_edit_serializer(self):
        return UserCompanyMemberEditSerializer


class CompanyMemberAdminEditSerializer(CompanyMemberEditSerializer):
    user = UserCompanyMemberAdminEditSerializer(partial=True)

    def get_user_edit_serializer(self):
        return UserCompanyMemberAdminEditSerializer


class CompanyMemberListSerializer(ListModelSerializer):
    user = UserDetailSerializer()
    venues = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = CompanyMember
        fields = ["user", "venues"]

    def get_select_related_fields(self):
        return ["user"]


class CompanyMemberDetailSerializer(ListModelSerializer):
    user = UserDetailSerializer()
    company = serializers.SerializerMethodField()

    class Meta:
        model = CompanyMember
        fields = ["user", "company", "active_venue"]

    def get_company(self, instance):
        from ..company.serializers import CompanyTitleSerializer
        return CompanyTitleSerializer(instance.company).data


class CompanyMemberAuthSerializer(CompanyMemberDetailSerializer):
    def get_company(self, instance):
        from ..company.serializers import CompanyCompanyMemberAuthSerializer
        return CompanyCompanyMemberAuthSerializer(instance.company).data


class CompanyMemberBasicDetailSerializer(ListModelSerializer):
    user = UserBasicDetailSerializer()

    class Meta:
        model = CompanyMember
        fields = ["user"]