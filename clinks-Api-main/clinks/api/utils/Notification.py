from rest_framework import status

from rest_framework.response import Response
from rest_framework.views import APIView

from push_notifications.models import APNSDevice, GCMDevice
from . import Constants

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


def send_order_for_customer(order_id, status_to_notify=None, delivery_status_to_notify=None):
    from ..order.models import Order

    title = None

    match status_to_notify:
        case Constants.ORDER_STATUS_ACCEPTED:
            title = "Your order is accepted"
        case Constants.ORDER_STATUS_REJECTED:
            title = "Your order is rejected"

    match delivery_status_to_notify:
        case Constants.DELIVERY_STATUS_OUT_FOR_DELIVERY:
            title = "Your order is out for delivery"
        case Constants.DELIVERY_STATUS_FAILED:
            title = "Your order is failed to be delivered"
        case Constants.DELIVERY_STATUS_DELIVERED:
            title = "Your order is delivered"

    if not title:
        return

    order = Order.objects.get(id=order_id)

    devices = get_devices(order.customer.user_id)

    data = {
        "type": Constants.NOTIFICATION_TYPE_ORDER,
        "order_id": order_id
    }

    send_bulk(title, title, data, devices["android"], devices["ios"])


def send_delivery_requests(delivery_requests):
    title = "There is a new delivery request in your area"

    data = {
        "type": Constants.NOTIFICATION_TYPE_ORDER_DELIVERY_REQUESTS
    }

    # Collect all devices
    all_android_devices = []
    all_ios_devices = []

    driver_ids = [delivery_request.driver.user_id for delivery_request in delivery_requests]
    logger.info(f"Sending notifications to drivers: {driver_ids}")

    for delivery_request in delivery_requests:
        devices = get_devices(delivery_request.driver.user_id)
        # Add to combined lists
        all_android_devices.extend(devices["android"])
        all_ios_devices.extend(devices["ios"])
    
    # Log device IDs before sending notifications
    logger.info(f"Android devices: {[device.id for device in all_android_devices]}")
    logger.info(f"iOS devices: {[device.id for device in all_ios_devices]}")

    send_bulk(title, title, data, android_devices=devices["android"], ios_devices=devices["ios"])



def send_returned_order_to_driver(order_id):
    from ..order.models import Order

    order = Order.objects.get(id=order_id)
    devices = get_devices(order.driver.user_id)
    title = f"{order.venue.title} has marked your latest order as returned"

    data = {
        "type": Constants.NOTIFICATION_TYPE_ORDER_RETURNED,
        "order_id": order_id
    }
    send_bulk(title, title, data, devices["android"], devices["ios"])


def send_bulk(title="", body="", data=None, android_devices=[], ios_devices=[], badge=0):
    if data:
        data.update({
            "title": title,
            "body": body
        })
    else:
        data = {
            "title": title,
            "body": body
        }

    mobile_push = {
        "badge": badge,
        "message": {
            "title": title,
            "body": body
        },
        "extra": data,
        "sound": "default"
    }

    if len(ios_devices) > 0:
        try:
            ios_devices.send_message(**mobile_push)
            logger.info(f"'send_notifications_in_bulk': Sending notifications to ios devices': {ios_devices}")
        except Exception as e:
            print("112> e", e)
            logger.error(f"'send_notifications_in_bulk': Error while sending notifications to ios devices: {e}")
            pass

    if len(android_devices) > 0:
        try:
            android_devices.send_message(**mobile_push)
            logger.info(f"'send_notifications_in_bulk': Sending notifications to android devices': {android_devices}")
        except Exception as e:
            logger.error(f"'send_notifications_in_bulk': Error while sending notifications to android devices: {e}")
            print("122> e", e)
            pass


def get_devices(user_id):
    android_devices = GCMDevice.objects.filter(user=user_id, active=True)
    ios_devices = APNSDevice.objects.filter(user=user_id, active=True)

    devices = {
        "android": android_devices,
        "ios": ios_devices
    }
    return devices


class SendNotification(APIView):

    def post(self, request):

        if "user_id" not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data["user_id"]

        devices = get_devices(user_id)
        android_devices = devices["android"]
        ios_devices = devices["ios"]

        title = request.data["title"] if "title" in request.data else "Test Message"
        body = request.data["body"] if "body" in request.data else "text"

        send_bulk(title, body, request.data, android_devices, ios_devices)

        return Response(status=status.HTTP_204_NO_CONTENT)
