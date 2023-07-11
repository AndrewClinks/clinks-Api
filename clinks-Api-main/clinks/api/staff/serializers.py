from ..utils.Serializers import serializers, ValidateModelSerializer, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from .models import Staff

from ..company_member.models import CompanyMember
from ..company_member.serializers import CompanyMemberBasicDetailSerializer


class StaffCreateSerializer(CreateModelSerializer):
    current_company_member = serializers.PrimaryKeyRelatedField(queryset=CompanyMember.objects.all(), required=False)

    class Meta:
        model = Staff
        fields = "__all__"

    def validate(self, attrs):
        venue = attrs["venue"]
        company_member = attrs["company_member"]
        current_company_member = attrs.pop("current_company_member", None)

        if current_company_member and current_company_member.company_id != venue.company_id:
            self.raise_validation_error("Staff", "You do not have access to this venue")

        if attrs["company_member"].company_id != venue.company_id:
            self.raise_validation_error("Staff", "This company member does not belong to this venue's company")

        if Staff.objects.filter(venue=venue, company_member=company_member).exists():
            self.raise_validation_error("Staff", "This company member is added as staff for this venue already")

        return attrs


class StaffListSerializer(ListModelSerializer):
    company_member = CompanyMemberBasicDetailSerializer()

    class Meta:
        model = Staff
        fields = "__all__"

    def get_select_related_fields(self):
        return ["company_member", ]


class StaffDetailSerializer(StaffListSerializer):
    pass
