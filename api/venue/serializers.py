from ..company.serializers import CompanyTitleSerializer
from ..utils.Serializers import serializers, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from ..address.serializers import Address, AddressCreateSerializer, AddressEditSerializer, AddressDetailSerializer
from ..opening_hour.serializers import (OpeningHour,
                                        OpeningHourValidateSerializer,
                                        OpeningHourCreateSerializer,
                                        OpeningHourEditSerializer,
                                        OpeningHourDetailSerializer,)

from ..currency.serializers import CurrencyDetailSerializer

from ..utils import List

from ..menu.models import Menu
from .models import Venue


class VenueCreateSerializer(CreateModelSerializer):
    address = AddressCreateSerializer()
    opening_hours = OpeningHourValidateSerializer(many=True)

    class Meta:
        model = Venue
        fields = ["title", "address", "company", "phone_country_code", "phone_number", "description", "opening_hours",]

    def create(self, validated_data):
        address_data = validated_data.pop("address")
        hours_data = validated_data.pop("opening_hours")

        serializer = AddressCreateSerializer(data=address_data)
        validated_data["address"] = serializer.create(address_data)

        venue = Venue.objects.create(**validated_data)

        save_opening_hours(venue, hours_data)

        venue.update_stats_on_create()

        Menu.objects.create(venue=venue)

        return venue


class VenueEditSerializer(EditModelSerializer):
    address = AddressEditSerializer(required=False, partial=True)
    opening_hours = OpeningHourValidateSerializer(many=True, required=False, partial=False)

    class Meta:
        model = Venue
        fields = ["title", "address", "phone_country_code", "phone_number", "description", "opening_hours", "paused"]

    def update(self, instance, validated_data):
        opening_hours_data = validated_data.pop("opening_hours", None)
        address_data = validated_data.pop("address", None)

        venue = super(VenueEditSerializer, self).update(instance, validated_data)

        if opening_hours_data is not None:
            save_opening_hours(venue, opening_hours_data)

        if address_data:
            Address.create_or_update_for(venue, address_data)
        return venue


class VenueAdminListSerializer(ListModelSerializer):
    address = AddressDetailSerializer()
    staff = serializers.SerializerMethodField()

    class Meta:
        model = Venue
        fields = ["id", "title", "address", "staff", "phone_country_code", "phone_number", "paused"]

    def get_staff(self, instance):
        from ..staff.serializers import Staff, StaffListSerializer
        staff = Staff.objects.filter(venue=instance.id)
        return StaffListSerializer(staff, many=True).data


class VenueMemberListSerializer(ListModelSerializer):
    from ..company.serializers import CompanyBasicInfoSerializer
    company = CompanyBasicInfoSerializer()
    address = AddressDetailSerializer()

    class Meta:
        model = Venue
        fields = ["id", "title", "address", "company", "paused"]

    def get_select_related_fields(self):
        return ["address", "company", ]


class VenueCustomerListSerializer(VenueMemberListSerializer):
    class Meta(VenueMemberListSerializer.Meta):
        fields = VenueMemberListSerializer.Meta.fields + ["service_fee_percentage"]


class VenueCustomerDistanceListSerializer(VenueCustomerListSerializer):
    distance = serializers.SerializerMethodField()
    delivery_fee = serializers.SerializerMethodField()

    class Meta(VenueCustomerListSerializer.Meta):
        fields = VenueCustomerListSerializer.Meta.fields + ["distance", "delivery_fee"]

    def get_distance(self, instance):
        if instance.distance is None:
            return None
        return instance.distance.m

    def get_delivery_fee(self, instance):
        from ..delivery_distance.models import DeliveryDistance
        distance = instance.distance
        if distance is None:
            return None
        return DeliveryDistance.get_by_distance(distance.m/1000).fee


class VenueMemberDetailSerializer(VenueMemberListSerializer):
    opening_hours = serializers.SerializerMethodField()
    staff = serializers.SerializerMethodField()
    currency = CurrencyDetailSerializer()

    class Meta(VenueMemberListSerializer.Meta):
        model = Venue
        fields = VenueMemberListSerializer.Meta.fields + ["opening_hours", "phone_country_code", "phone_number",
                                                          "description", "staff", "sales_count", "total_earnings",
                                                          "currency"]

    def get_opening_hours(self, instance):
        opening_hours = self.instance.opening_hours.order_by("order")
        return OpeningHourDetailSerializer(opening_hours, many=True).data

    def get_staff(self, instance):
        from ..staff.serializers import Staff, StaffListSerializer
        staff = Staff.objects.filter(venue=instance.id)
        return StaffListSerializer(staff, many=True).data


class VenueAdminDetailSerializer(VenueMemberDetailSerializer):
    class Meta(VenueMemberDetailSerializer.Meta):
        fields = VenueMemberDetailSerializer.Meta.fields + ["total_earnings", "sales_count", "average_delivery_time"]


class VenueCustomerDetailSerializer(VenueCustomerListSerializer):
    class Meta(VenueCustomerListSerializer.Meta):
        fields = VenueCustomerListSerializer.Meta.fields + ["service_fee_percentage"]


class VenueOrderDetailSerializer(ListModelSerializer):
    address = AddressDetailSerializer()

    class Meta:
        model = Venue
        fields = ["id", "title", "address", "phone_country_code", "phone_number"]


class VenueOrderDriverDetailSerializer(ListModelSerializer):
    class Meta:
        model = Venue
        fields = ["id", "title", "phone_country_code", "phone_number"]


class VenueOrderAdminDetailSerializer(VenueOrderDetailSerializer):
    company = CompanyTitleSerializer(read_only=True)
    contact_email = serializers.SerializerMethodField()

    class Meta(VenueOrderDetailSerializer.Meta):
        fields = VenueOrderDetailSerializer.Meta.fields + ["company", "contact_email"]

    def get_contact_email(self, instance):
        company_member = instance.company.members.first()
        return company_member.user.email if company_member else None



def save_opening_hours(venue, opening_hours_data):

    venue.opening_hours.all().delete()

    List.remove_duplicates(opening_hours_data, "day")

    opening_hours_data = OpeningHour.get_ordered_by_date(opening_hours_data)

    order = 0
    for opening_hour_data in opening_hours_data:
        opening_hour_data["venue"] = venue
        opening_hour_data["order"] = order

        if "id" in opening_hour_data:
            opening_hour_data["deleted_at"] = None
            id = opening_hour_data["id"]
            hour = OpeningHour.all_objects.get(id=id)
            serializer = OpeningHourEditSerializer(data=opening_hour_data)
            serializer.update(hour, opening_hour_data)
        else:
            serializer = OpeningHourCreateSerializer(data=opening_hour_data)
            serializer.create(opening_hour_data)

        order += 1

    return venue

