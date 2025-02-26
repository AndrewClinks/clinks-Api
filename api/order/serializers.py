from ..utils.Serializers import serializers, CreateModelSerializer, EditModelSerializer, ListModelSerializer

from ..address.models import Address
from ..address.serializers import AddressDetailSerializer
from ..menu.models import Menu
from ..menu.serializers import MenuDetailSerializer
from ..menu_item.models import MenuItem
from ..venue.serializers import VenueOrderDetailSerializer, VenueOrderAdminDetailSerializer, VenueOrderDriverDetailSerializer
from ..venue.models import Venue
from ..setting.models import Setting
from ..delivery_distance.models import DeliveryDistance
from django.contrib.gis.geos import Point

from ..identification.serializers import IdentificationCreateSerializer

from ..payment.serializers import PaymentValidateSerializer, PaymentCreateSerializer, PaymentOrderDetailSerializer, PaymentOrderDriverDetailSerializer
from ..customer.serializers import CustomerOrderDetailSerializer
from ..driver.serializers import DriverOrderDetailSerializer

from ..order_item.serializers import OrderItemValidateSerializer, OrderItemDetailSerializer
from ..tasks import update_stats_for_order, create_delivery_requests, send_notification, generate_receipt_for_order
import secrets

from ..utils import Availability, List, Distance, DateUtils, Constants, Api
from ..order.models import Order
from ..delivery_request.models import DeliveryRequest
from ..payment.models import Payment
from ..currency.models import Currency 
from ..card.models import Card
from ..card.serializers import CardDetailSerializer
from ..driver.models import Driver

import logging
logger = logging.getLogger('clinks-api-live')

class OrderCreateSerializer(CreateModelSerializer):
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())
    menu = serializers.PrimaryKeyRelatedField(queryset=Menu.objects.all())
    items = OrderItemValidateSerializer(many=True, allow_null=False, allow_empty=False)
    payment = PaymentValidateSerializer()

    def get_address(self, obj):
        logger.info(f"OrderCreateSerializer get_customer_address called {obj}")
        try:
            return AddressDetailSerializer(obj.customer.address).data  # Adjust based on your structure
        except AttributeError as e:
            # Log to confirm where the access issue arises
            logger.error(f"Error accessing address: {e}")
            return None
    
    def get_menu(self, obj):
        """Retrieve menu data from the Order instance."""
        menu = obj.menu  # Accesses the `menu` property on the Order model
        return MenuDetailSerializer(menu).data if menu else None  # Serialise if exists

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Call the superclass initializer
        # logger.info("OrderCreateSerializer instantiated with context: %s", self.context)
        logger.info("OrderCreateSerializer initial data: %s", self.initial_data)

    class Meta:
        model = Order
        fields = ["customer", "venue", "address", "menu", "payment", "items"]

    def validate(self, attrs):
        customer = attrs["customer"]
        address = attrs["address"]
        venue = attrs["venue"]
        menu = attrs["menu"]
        items = attrs["items"]
        is_test_order = self.context.get('is_test_order', False)

        # Log the address object to check if it is being retrieved properly
        logger.info(
            "OrderCreateSerializer address retrieved: id=%s, line_1=%s, city=%s, state=%s, country=%s, point=%s",
            address.id, address.line_1, address.city, address.state, address.country, address.point
        )

        if not is_test_order:
            status = Availability.status()

            if venue.company.status != Constants.COMPANY_STATUS_ACTIVE:
                self.raise_validation_error("Order", "Sorry, this company isn't active!")

            if venue.paused:
                self.raise_validation_error("Order", "Sorry, this venue isn't active!")

            if status["available"] is False:
                self.raise_validation_error("Order", status["reason"])

            if not venue.open():
                self.raise_validation_error("Order", "Venue is closed")

            if not venue.company.can_accept_payments():
                self.raise_validation_error("Order", "This company cannot accept payments yet!")
            
            if customer.address != address:
                self.raise_validation_error("Order", "This address does not belong to you")

            if not venue.can_deliver_to(customer.address):
                self.raise_validation_error("Order", "Venue does not deliver to your location")

        if menu.venue != venue:
            self.raise_validation_error("Order", "This menu does not belong to this venue")

        unique_item_ids = List.get_unique_item_ids(items)

        count_of_items = MenuItem.objects.filter(id__in=unique_item_ids, menu=menu).count()

        if len(unique_item_ids) != count_of_items:
            self.raise_validation_error("Order", "You have menu item does not belong to current venue")

        subtotal = self.calculate_subtotal(items)

        if subtotal < Setting.get_minimum_order_amount():
            self.raise_validation_error("Order", "Minimum order value has not reached")

        #This creates an api_payment entry during validation of the order
        logger.info(f"Attributes sent to pay method: {attrs}")
        # logger.info(f"Subtotal sent to pay method: {subtotal}")

        # The payment is created here, if its not successful then the order is not created
        self.pay(attrs, subtotal)
        return attrs

    def calculate_subtotal(self, items):
        subtotal = 0

        for item in items:
            price = item["price_sale"] if item["price_sale"] is not None else item["price"]
            total_item_price = price * item["quantity"]
            subtotal += total_item_price

        return subtotal

    def pay(self, attrs, subtotal):
        venue = attrs["venue"]
        customer = attrs["customer"]
        menu = attrs.pop("menu") # This needs to be popped because it's not a field on the Order model

        # Check if it's a test order
        is_test_order = self.context.get('is_test_order', False)

        if is_test_order:
            delivery_distance = DeliveryDistance.get_by_distance(0)
        else:
            delivery_distance = DeliveryDistance.get_by_distance(Distance.between(venue.address.point, customer.address.point, True))


        service_fee_percentage = venue.service_fee_percentage
        service_fee = int(round(subtotal * service_fee_percentage))

        if service_fee < 50:
            service_fee = 50

        if service_fee > 200:
            service_fee = 200

        payment_data = attrs["payment"]

        payment_data["delivery_fee"] = delivery_distance.fee
        payment_data["delivery_driver_fee"] = delivery_distance.driver_fee
        payment_data["service_fee"] = service_fee
        payment_data["amount"] = subtotal
        payment_data["currency"] = venue.currency.id
        payment_data["customer"] = customer
        payment_data["company"] = venue.company.id

        ## !!!!! TEST ORDER PAYMENT !!!!!
        if is_test_order:
            # Hard coding values directly to the Payment model instead of using PaymentCreateSerializer
            # This should make it appear as if this is a second call that is validating the payment
            # Fetch a mock card instance, assuming '16' is the ID of the card you want to use
            mock_card = Card.objects.get(id=1)

            # Fetch a mock currency instance, assuming '1' is the ID of the currency you want to use
            mock_currency = Currency.objects.get(id=1)

            # If it's a test order, mock the payment data as if this 
            payment_data["stripe_charge_id"] = "mock_stripe_charge_id"  # Mock charge ID
            payment_data["paid_at"] = DateUtils.now()  # Mock payment timestamp
            payment_data["card"] = mock_card
            payment_data["currency"] = mock_currency 
            payment_data["company"] = venue.company 
            # Calculate the total amount
            total_amount = payment_data["amount"] + payment_data.get("tip", 0) + payment_data.get("service_fee", 0) + payment_data.get("delivery_fee", 0)
            payment_data["total"] = total_amount  # Ensure total is set
            payment_data.pop('expected_price', None)  # Remove the expected price from the payment data

            # Create a mock Payment object complete with the stripe_charge_id
            payment = Payment.objects.create(**payment_data)
        else:
            # This is where it goes off to stripe so be careful with this
            # The PaymentCreateSerializer differentiates between the two calls
            serializer = PaymentCreateSerializer(data=payment_data)
            
            # If not valid then I think this function doesnt complete?
            serializer.is_valid(raise_exception=True)
            logger.info(f"OrderCreateSerializer.validated_data: {serializer.validated_data}")
            payment = serializer.create(serializer.validated_data)
        
        attrs["payment"] = payment
        return payment

    def create(self, validated_data):
        logger.info("Starting order creation process")

        # get_data logs the validated_data and 
        validated_data["data"] = self.get_data(validated_data)
        logger.debug("Data after get_data: %s", validated_data["data"])

        validated_data["driver_verification_number"] = secrets.randbelow(100)
        logger.debug("Driver verification number: %s", validated_data["driver_verification_number"])

        # Log the final validated data before creating the order
        # logger.info("Final validated_data before creating order: %s", validated_data)

        # Create the order in the db!!!
        # there is a constraint on the api_order table that stops 2 orders with same payment_intent_id
        # I think this is how it stops the same order being created twice with the second call
        # But that would throw an integrity error from the db so I'm not sure.
        # TODO: confirm that this is called twice during a real order, and whether there is a db error
        order = Order.objects.create(**validated_data)
        logger.info("Order created with ID: %s", order.id)
        logger.debug("Order instance fields: %s", vars(order))

        # Queue tasks and log their queuing
        update_stats_for_order.delay_on_commit(order.id)
        logger.info("Queued update_stats_for_order task for order ID: %s", order.id)

        generate_receipt_for_order.delay_on_commit(order.id)
        logger.info("Queued generate_receipt_for_order task for order ID: %s", order.id)

        return order

    def get_data(self, validated_data):
        logger.info("Starting get_data method")

        # Log the initial validated data
        logger.debug("Initial validated_data: %s", validated_data)

        # Extract and log individual components
        address = validated_data.pop("address")
        logger.debug("Extracted address: %s", address)

        card = validated_data["payment"].card
        logger.debug("Extracted card: %s", card)

        venue = validated_data["venue"]
        logger.debug("Extracted venue: %s", venue)

        items = validated_data.pop("items")
        logger.debug("Extracted items: %s", items)

        data = dict()

        # Serialize and log each component
        data["customer_address"] = AddressDetailSerializer(address).data
        logger.debug("Serialized customer_address: %s", data["customer_address"])

        data["card"] = CardDetailSerializer(card).data
        logger.debug("Serialized card: %s", data["card"])

        data["venue_address"] = AddressDetailSerializer(venue.address).data
        logger.debug("Serialized venue_address: %s", data["venue_address"])

        data["items"] = OrderItemDetailSerializer(items, many=True).data
        logger.debug("Serialized items: %s", data["items"])

        data["distance"] = Distance.between(venue.address.point, address.point)
        logger.debug("Calculated distance: %s", data["distance"])

        logger.info("Completed get_data method")

        return data


class OrderCompanyMemberEditSerializer(EditModelSerializer):
    # Parent of Detail is SmartDetailAPIView 
    # Parent first calls validate and then update in quick succession
    class Meta:
        model = Order
        fields = ["status", "delivery_status", "driver"]

    def validate_driver(self, driver):
        if driver is None:
            return None
        if isinstance(driver, int):
            # Fetch the Driver instance from the database
            try:
                driver = Driver.objects.get(pk=driver)
            except Driver.DoesNotExist:
                self.raise_validation_error("driver", "Invalid driver ID")
        elif not isinstance(driver, Driver):
            self.raise_validation_error("driver", "Invalid driver input")
        return driver
    
    def validate_status(self, status):
        return self.validate_enum_field("status", status, [Constants.ORDER_STATUS_LOOKING_FOR_DRIVER, Constants.ORDER_STATUS_REJECTED, Constants.ORDER_STATUS_ACCEPTED])

    def validate_delivery_status(self, delivery_status):
        return self.validate_enum_field("delivery status", delivery_status, [Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY, Constants.DELIVERY_STATUS_RETURNED, Constants.DELIVERY_STATUS_DELIVERED])

    def validate(self, attrs):
        # Log validation start and the provided attributes
        # logger.info(f"Starting validation for Order {self.instance.id} with attrs: {attrs}")
        
        status = attrs.get("status", None)
        delivery_status = attrs.get("delivery_status", None)
        driver = attrs.get("driver", None)

        if status and delivery_status:
            self.raise_validation_error("Order", "You cannot edit status and delivery status at the same time")

        if status == Constants.ORDER_STATUS_ACCEPTED and not driver:
            self.raise_validation_error("Driver", "Driver must be specified when accepting an order")

        if status == Constants.ORDER_STATUS_REJECTED and (self.instance.delivery_status != Constants.DELIVERY_STATUS_PENDING or self.instance.driver != None):
            self.raise_validation_error("Order", "You cannot reject this order because the driver is trying to deliver it")

        if delivery_status is not None:
            if self.instance.driver is None:
                self.raise_validation_error("Order", "Order has to have a driver assigned to change delivery status")

            if delivery_status == Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY and self.instance.delivery_status != Constants.DELIVERY_STATUS_PENDING:
                self.raise_validation_error("Order", "Once delivered delivery status must be marked as pending first then delivered once code is provided")

            if delivery_status == Constants.DELIVERY_STATUS_RETURNED and self.instance.delivery_status != Constants.DELIVERY_STATUS_FAILED:
                self.raise_validation_error("Order", "Returned orders must be marked as delivery status failed")

        now = DateUtils.now()
        if status == Constants.ORDER_STATUS_LOOKING_FOR_DRIVER:
            # logger.info(f"Order {self.instance.id} marked as LOOKING_FOR_DRIVER, setting started_looking_for_drivers_at")
            attrs["started_looking_for_drivers_at"] = now
        elif status == Constants.ORDER_STATUS_REJECTED:
            # logger.info(f"Order {self.instance.id} marked as ORDER_STATUS_REJECTED, refunding")
            attrs["rejected_at"] = now
            attrs["rejection_reason"] = Constants.ORDER_REJECTION_REASON_REJECTED_BY_VENUE
            self.instance.payment.refund()

        if delivery_status == Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY:
            # logger.info(f"Order {self.instance.id} marked as DELIVERY_STATUS_OUT_FOR_DELIVERY")
            attrs["collected_at"] = now
        elif delivery_status == Constants.DELIVERY_STATUS_RETURNED:
            # logger.info(f"Order {self.instance.id} marked as DELIVERY_STATUS_RETURNED")
            attrs["returned_at"] = now
            self.instance.payment.returned(self.instance)
        
        if status == Constants.ORDER_STATUS_ACCEPTED and self.context['request'].user.role != Constants.USER_ROLE_ADMIN:
            self.raise_validation_error("Order", "You must be admin to change an order to accepted directly.")

        return attrs

    # For Accept/Reject
    def update(self, instance, validated_data):
        # logger.info(f"Updating Order {instance.id} with validated_data: {validated_data}")

        # If not in the request then set to None but doesnt change db value.
        status = validated_data.get("status", None)
        delivery_status = validated_data.get("delivery_status", None)
        driver = validated_data.get("driver", None)

        try:
            # Updates either status or delivery_status can't be both at the same time
            # Updates status = Constants.ORDER_STATUS_LOOKING_FOR_DRIVER or Constants.ORDER_STATUS_REJECTED
            # Updates delivery_status = Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY or Constants.DELIVERY_STATUS_RETURNED
            order = super(OrderCompanyMemberEditSerializer, self).update(instance, validated_data)
            logger.info(f"Order {order.id} status updated to {order.status}")

            if status is Constants.ORDER_STATUS_LOOKING_FOR_DRIVER:
                #logger.info(f"Updating {order.id} ORDER_STATUS_LOOKING_FOR_DRIVER create_delivery_requests")
                # Using delay instead of delay_on_commit because there can be some lag on this task
                # and it blocks the http response.
                create_delivery_requests.delay(order.id)

            if status is Constants.ORDER_STATUS_LOOKING_FOR_DRIVER or status is Constants.ORDER_STATUS_REJECTED:
                #logger.info(f"Updating {order.id} ORDER_STATUS_LOOKING_FOR_DRIVER or ORDER_STATUS_REJECTED update_stats_for_order")
                update_stats_for_order.delay_on_commit(order.id)

            if status == Constants.ORDER_STATUS_REJECTED:
                #logger.info(f"Updating {order.id} ORDER_STATUS_REJECTED send_notification")
                send_notification.delay_on_commit("send_order_for_customer", order.id, status)

            # This allows manual setting of the order to a specific driver
            if status == Constants.ORDER_STATUS_ACCEPTED and self.context['request'].user.role == Constants.USER_ROLE_ADMIN:
                if driver:
                    # Update the order with the new driver's ID
                    order.driver = driver
                    order.accepted_at = DateUtils.now()
                    order.status = Constants.ORDER_STATUS_ACCEPTED
                    order.save(update_fields=["driver", "accepted_at", "status"]) 

                    # Check if there's an existing delivery request for this driver and this order
                    delivery_request = DeliveryRequest.objects.filter(order=order, driver=order.driver).first()
                    
                    if delivery_request:
                        # Update the status of the existing delivery request
                        delivery_request.status = Constants.DELIVERY_REQUEST_STATUS_ACCEPTED
                        delivery_request.save()
                    else:
                        venue_point = Point(order.data["venue_address"]["longitude"], order.data["venue_address"]["latitude"])
                        # Create a new delivery request for this driver and this order
                        delivery_request = DeliveryRequest.objects.create(
                            order=order, 
                            driver=order.driver, 
                            status=Constants.DELIVERY_REQUEST_STATUS_ACCEPTED,
                            driver_location=venue_point
                        )

                    # Set all other delivery requests for this order to "missed"
                    DeliveryRequest.objects.filter(order=order).exclude(
                        driver=order.driver
                    ).update(status=Constants.DELIVERY_REQUEST_STATUS_MISSED)

                    # Update the driver with the order
                    order.driver.current_delivery_request = delivery_request
                    order.driver.save()


            if delivery_status is Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY:
                #logger.info(f"Updating {order.id} DELIVERY_STATUS_OUT_FOR_DELIVERY delay_on_commit")
                send_notification.delay_on_commit("send_order_for_customer", order.id, None, delivery_status)

            if delivery_status == Constants.DELIVERY_STATUS_RETURNED:
                #logger.info(f"Updating {order.id} DELIVERY_STATUS_RETURNED delay_on_commit driver.current_delivery_request = None")
                driver.current_delivery_request = None
                driver.save()

                send_notification.delay_on_commit("send_returned_order_to_driver", order.id)

            return order
        except Exception as e:
            logger.error(f"Error updating Order {instance.id}: {str(e)}")
            raise
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        address_data = instance.data.get("customer_address", {})
        representation["address"] = {
            "line_1": address_data.get("line_1"),
            "city": address_data.get("city"),
            "state": address_data.get("state"),
            "country": address_data.get("country"),
        }
        return representation


class OrderDriverEditSerializer(EditModelSerializer):
    delivery_status = serializers.CharField()
    identification_status = serializers.CharField()
    identification = IdentificationCreateSerializer(required=False)
    driver_location_latitude = serializers.FloatField(required=False)
    driver_location_longitude = serializers.FloatField(required=False)

    class Meta:
        model = Order
        fields = ["delivery_status", "identification", "identification_status", "driver_location_latitude", "driver_location_longitude", "no_answer_image"]

    def validate_delivery_status(self, delivery_status):
        return self.validate_enum_field("delivery_status", delivery_status, [Constants.DELIVERY_STATUS_FAILED, Constants.DELIVERY_STATUS_DELIVERED])

    def validate_identification_status(self, identification_status):
        return self.validate_enum_field("identification_status", identification_status, Constants.ORDER_IDENTIFICATION_STATUSES)

    def validate(self, attrs):
        identification_status = attrs.get("identification_status", None)
        identification = attrs.get("identification", None)
        identification_required = is_identification_required(self.instance)
        delivery_status = attrs.get("delivery_status", None)
        no_answer_image = attrs.get("no_answer_image", None)
        driver_location_latitude = attrs.pop("driver_location_latitude", None)
        driver_location_longitude = attrs.pop("driver_location_longitude", None)

        delivered = delivery_status == Constants.DELIVERY_STATUS_DELIVERED
        id_provided = identification_status == Constants.ORDER_IDENTIFICATION_STATUS_PROVIDED
        id_refused = identification_status == Constants.ORDER_IDENTIFICATION_STATUS_REFUSED
        id_not_requested = identification_status == Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUESTED
        id_not_provided = identification_status == Constants.ORDER_IDENTIFICATION_STATUS_NOT_PROVIDED
        id_not_required = identification_status == Constants.ORDER_IDENTIFICATION_STATUS_NOT_REQUIRED

        if not identification_status:
            self.raise_validation_error("Order", "identification_status is required")

        if not delivery_status:
            self.raise_validation_error("Order", "delivery_status is required")

        if self.instance.status != Constants.ORDER_STATUS_ACCEPTED:
            self.raise_validation_error("Order", "Order needs to be accepted first!")

        if self.instance.delivery_status != Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY:
            self.raise_validation_error("Order", "Order status has to be out for delivery")

        if id_provided and not identification:
            self.raise_validation_error("Order",
                                        "Identification status is set to 'provided' without providing an identification")

        if id_provided and identification and not delivered:
            self.raise_validation_error("Order", "You cannot set delivery status as 'failed' when ID is provided")

        if id_refused and delivered:
            self.raise_validation_error("Order", "You cannot set delivery status as 'delivered' when customer refused to provide an ID")

        if delivered and identification_required and (not id_provided and not id_not_requested and not id_not_required):
            self.raise_validation_error("Order",
                                        "Identification is required for this order")

        if id_not_requested and not delivered:
            self.raise_validation_error("Order",
                                        "You cannot set delivery status as 'failed' when ID is not requested")

        if id_not_required and not delivered:
            self.raise_validation_error("Order",
                                        "You cannot set delivery status as 'failed' when ID is not required")

        if id_provided and identification and not delivered:
            self.raise_validation_error("Order",
                                        "You cannot set delivery status as 'failed' when ID is provided")

        if id_not_provided:
            if delivered:
                self.raise_validation_error("Order",
                                        "You cannot set delivery status as 'delivered' when customer does not provide an ID")

            if not no_answer_image or not driver_location_longitude or not driver_location_latitude:
                self.raise_validation_error("Order", "no_answer_image and driver_location are required when 'no answer' is selected")

            driver_point = Point(driver_location_longitude, driver_location_latitude)
            customer_address = self.instance.data["customer_address"]
            customer_point = Point(customer_address["longitude"], customer_address["latitude"])

            distance_of_driver_to_customer = Distance.between(driver_point, customer_point, True)

            if distance_of_driver_to_customer > Api.NO_ANSWER_DISTANCE_TO_CUSTOMER_IN_KMS:
                self.raise_validation_error("Order", f"You are not close enough to customer to set order as 'no answer'")

            attrs["no_answer_driver_location"] = driver_point

        if not id_not_provided:
            attrs.pop("no_answer_image", None)

        now = DateUtils.now()
        if delivery_status == Constants.ORDER_STATUS_LOOKING_FOR_DRIVER:
            attrs["started_looking_for_drivers_at"] = now
        elif delivery_status == Constants.ORDER_STATUS_REJECTED:
            attrs["rejected_at"] = now
            attrs["rejection_reason"] = Constants.ORDER_REJECTION_REASON_REJECTED_BY_VENUE
            self.instance.payment.refund()
        return attrs

    def update(self, instance, validated_data):
        from ..driver_payment.models import DriverPayment

        delivery_status = validated_data["delivery_status"]
        identification_data = validated_data.pop("identification", None)

        if identification_data:
            serializer = IdentificationCreateSerializer(data=identification_data)
            validated_data["identification"] = serializer.create(identification_data)

        order = super(OrderDriverEditSerializer, self).update(instance, validated_data)

        if delivery_status == Constants.DELIVERY_STATUS_DELIVERED:
            update_stats_for_order.delay_on_commit(order.id)
            driver = order.driver
            driver.current_delivery_request = None
            driver.save()

        if delivery_status == Constants.DELIVERY_STATUS_FAILED or delivery_status == Constants.DELIVERY_STATUS_DELIVERED:
            send_notification.delay_on_commit("send_order_for_customer", order.id, None, delivery_status)

        DriverPayment.create(self.instance, Constants.DRIVER_PAYMENT_TYPE_DELIVERY)

        return order


class OrderAdminListSerializer(ListModelSerializer):
    venue = VenueOrderAdminDetailSerializer(read_only=True)
    payment = PaymentOrderDetailSerializer(read_only=True)
    customer = CustomerOrderDetailSerializer(read_only=True)
    driver = DriverOrderDetailSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "venue", "data", "status", "delivery_status", "payment", "created_at", "customer", "driver",
                  "identification_status", "identification"]

    def get_select_related_fields(self):
        return ["venue", "payment", "customer", "driver"]


class OrderCompanyMemberListSerializer(ListModelSerializer):
    customer = CustomerOrderDetailSerializer()
    driver = DriverOrderDetailSerializer()
    payment = PaymentOrderDetailSerializer()
    total_item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "customer", "data", "driver", "status", "delivery_status", "payment", "total_item_count", "created_at", "driver_verification_number", "receipt"]

    def get_total_item_count(self, instance):
        total_item_count = 0

        for item in instance.data["items"]:
            total_item_count += item["quantity"]

        return total_item_count

    def get_select_related_fields(self):
        return ["payment", "customer", "driver"]


class OrderCustomerListSerializer(ListModelSerializer):
    venue = VenueOrderDetailSerializer()
    payment = PaymentOrderDetailSerializer()

    class Meta:
        model = Order
        fields = ["id", "venue", "data", "payment",  "created_at", "status", "delivery_status"]

    def get_select_related_fields(self):
        return ["payment", "venue"]


class OrderDriverListSerializer(ListModelSerializer):
    data = serializers.SerializerMethodField()
    payment = PaymentOrderDriverDetailSerializer()

    class Meta:
        model = Order
        fields = ["id", "payment", "data"]

    def get_data(self, instance):
        data = {
            "customer_address": instance.data["customer_address"],
            "venue_address": instance.data["venue_address"]
        }
        return data


class OrderPaymentListSerializer(ListModelSerializer):

    class Meta:
        model = Order
        fields = ["id", "status", "delivery_status"]


class OrderAdminDetailSerializer(OrderAdminListSerializer):
    pass


class OrderCompanyMemberDetailSerializer(OrderCompanyMemberListSerializer):
    pass


class OrderCustomerDetailSerializer(OrderCustomerListSerializer):
    pass


class OrderDriverDetailSerializer(OrderDriverListSerializer):
    identification_required = serializers.SerializerMethodField()
    customer_phone_number = serializers.SerializerMethodField()
    venue_phone_number = serializers.SerializerMethodField()
    venue = VenueOrderDriverDetailSerializer()

    class Meta(OrderDriverListSerializer.Meta):
        fields = OrderDriverListSerializer.Meta.fields + ["driver_verification_number", "identification_required", "status", "delivery_status",
                                                          "customer_phone_number", "venue_phone_number", "venue"]

    def get_identification_required(self, instance):
        return is_identification_required(instance)

    def get_customer_phone_number(self, instance):
        customer_user = instance.customer.user
        if not customer_user.phone_number:
            return None

        return f"{customer_user.phone_country_code}{customer_user.phone_number}"

    def get_venue_phone_number(self, instance):
        venue = instance.venue
        return f"{venue.phone_country_code}{venue.phone_number}"

def is_identification_required(order):
    identification_required = DateUtils.year_difference_to_now(order.customer.user.date_of_birth) < Setting.get_minimum_age()
    return identification_required



