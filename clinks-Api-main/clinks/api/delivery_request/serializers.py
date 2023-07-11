from ..utils.Serializers import CreateModelSerializer, EditModelSerializer, ListModelSerializer

from .models import DeliveryRequest

from ..order.serializers import OrderDriverListSerializer, OrderDriverDetailSerializer

from ..utils import Constants, DateUtils

from ..tasks import set_delivery_requests_as_missed


class DeliveryRequestEditSerializer(EditModelSerializer):

    class Meta:
        model = DeliveryRequest
        fields = ["status", "driver_location", "driver"]

    def validate_status(self, status):
        return self.validate_enum_field("status", status, [Constants.DELIVERY_REQUEST_STATUS_ACCEPTED, Constants.DELIVERY_REQUEST_STATUS_REJECTED])

    def validate(self, attrs):
        driver = attrs["driver"]
        order = self.instance.order
        status = attrs["status"]

        accepted = status == Constants.DELIVERY_REQUEST_STATUS_ACCEPTED

        if self.instance.status != Constants.DELIVERY_REQUEST_STATUS_PENDING:
            self.raise_validation_error("DeliveryRequest", f"You can only accept or reject pending delivery requests")

        if accepted and driver.has_ongoing_delivery():
            self.raise_validation_error("DeliveryRequest", "You can't accept another delivery before finishing up with current order")

        if accepted and order.driver is not None:
            self.raise_validation_error("DeliveryRequest", "This request already accepted by different driver")

        if accepted and order.status != Constants.ORDER_STATUS_LOOKING_FOR_DRIVER:
            self.raise_validation_error("DeliveryRequest", "This order is not looking for drivers")

        if accepted:
            attrs["accepted_at"] = DateUtils.now()
        else:
            attrs["rejected_at"] = DateUtils.now()

        return attrs

    def update(self, instance, validated_data):
        delivery_request = super(DeliveryRequestEditSerializer, self).update(instance, validated_data)

        if delivery_request.status == Constants.DELIVERY_REQUEST_STATUS_ACCEPTED:
            delivery_request.order.accepted(delivery_request)

            set_delivery_requests_as_missed.delay_on_commit(delivery_request.order.id)

        return delivery_request


class DeliveryRequestListSerializer(ListModelSerializer):
    order = OrderDriverDetailSerializer()

    class Meta:
        model = DeliveryRequest
        fields = ["id", "status", "order", "driver", "rejected_at", "accepted_at"]

    def get_select_related_fields(self):
        return ["order"]


class DeliveryRequestDetailSerializer(DeliveryRequestListSerializer):
    order = OrderDriverDetailSerializer()


class DeliveryRequestDriverDetailSerializer(ListModelSerializer):

    class Meta:
        model = DeliveryRequest
        fields = ["id", "order"]