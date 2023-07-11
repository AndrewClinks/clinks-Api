from ..utils.Serializers import serializers, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from ..company_member.serializers import CompanyMemberValidateSerializer, CompanyMemberCreateSerializer
from ..image.serializers import ImageDetailSerializer
from ..all_time_stat.models import AllTimeStat

from ..utils import Constants

from .models import Company


class CompanyCreateSerializer(CreateModelSerializer):
    members = CompanyMemberValidateSerializer(many=True, allow_empty=False)

    class Meta:
        model = Company
        fields = ["title", "featured_image", "logo", "eircode", "vat_no", "liquor_license_no", "members"]

    def create(self, validated_data):
        members_data = validated_data.pop("members")

        company = Company.objects.create(**validated_data)

        for index, member_data in enumerate(members_data):
            member_data["company"] = company
            serializer = CompanyMemberCreateSerializer(data=member_data)
            company_member = serializer.create(member_data)

            if index == 0:
                company_member.role = Constants.COMPANY_MEMBER_ROLE_ADMIN
                company_member.save()

            AllTimeStat.update(Constants.ALL_TIME_STAT_TYPE_COMPANY_COUNT, Company.objects.count(), True)

        return company


class CompanyEditSerializer(EditModelSerializer):

    class Meta:
        model = Company
        fields = ["title", "logo", "featured_image"]


class CompanyAdminEditSerializer(CompanyEditSerializer):
    status = serializers.CharField(required=False)

    class Meta(CompanyEditSerializer.Meta):
        fields = CompanyEditSerializer.Meta.fields + ["eircode", "vat_no", "liquor_license_no", "status"]

    def validate_status(self, status):
        return self.validate_enum_field("status", status, [Constants.COMPANY_STATUS_ACTIVE, Constants.COMPANY_STATUS_PAUSED])

    def validate(self, attrs):
        if self.instance.status == Constants.COMPANY_STATUS_SETUP_NOT_COMPLETED and "status" in attrs:
            self.raise_validation_error("Company", "status cannot be changed while company is in setup stage")

        return attrs


class CompanyBasicInfoSerializer(ListModelSerializer):
    logo = ImageDetailSerializer()
    featured_image = ImageDetailSerializer()

    class Meta:
        model = Company
        fields = ["id", "title", "logo", "featured_image", ]


class CompanyCompanyMemberAuthSerializer(ListModelSerializer):
    logo = ImageDetailSerializer()
    featured_image = ImageDetailSerializer()
    stripe_connected = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ["id", "title", "logo", "featured_image", "venue_count", "has_added_menu_items", "stripe_connected", "stripe_verification_status"]

    def get_stripe_connected(self, instance):
        return instance.stripe_account_id is not None


class CompanyTitleSerializer(ListModelSerializer):

    class Meta:
        model = Company
        fields = ["id", "title", ]


class CompanyListSerializer(CompanyBasicInfoSerializer):
    venues = serializers.SerializerMethodField()

    class Meta(CompanyBasicInfoSerializer.Meta):
        model = Company
        fields = CompanyBasicInfoSerializer.Meta.fields + ["total_earnings", "venues", "status"]

    def get_venues(self, instance):
        from ..venue.serializers import Venue, VenueAdminListSerializer
        venues = Venue.objects.filter(company_id=instance.id)
        return VenueAdminListSerializer(venues, many=True).data

    def get_select_related_fields(self):
        return ["logo", "featured_image"]


class CompanyDetailSerializer(CompanyListSerializer):
    stripe_connected = serializers.SerializerMethodField()

    class Meta(CompanyListSerializer.Meta):
        fields = CompanyListSerializer.Meta.fields + ["sales_count", "average_delivery_time", "venue_count",
                                                      "stripe_connected", "has_added_menu_items", "stripe_verification_status"]

    def get_stripe_connected(self, instance):
        return instance.stripe_account_id is not None


class CompanyAdminDetailSerializer(CompanyDetailSerializer):

    class Meta(CompanyDetailSerializer.Meta):
        fields = CompanyDetailSerializer.Meta.fields + ["eircode", "vat_no", "liquor_license_no", "status"]


class CompanyAdminPasscodeDetailSerializer(ListModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "title", "passcode"]

