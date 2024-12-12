from celery.schedules import crontab
from celery import Task, shared_task
from celery import Celery
from celery.utils.log import get_task_logger
from celery import shared_task
from django.db import transaction

from .utils import Constants, Api


from .utils import Mail

logger = get_task_logger(__name__)
app = Celery('clinks')

class TransactionAwareTask(Task):
    def delay_on_commit(self, *args, **kwargs):
        return transaction.on_commit(
            lambda: self.delay(*args, **kwargs)
        )


@shared_task(
    name="send_mail",
    ignore_result=True,
    base=TransactionAwareTask
)
def send_mail(mail_function_to_be_triggered, *args):
    logger.info(f"Start > send_mail with function: {mail_function_to_be_triggered}")

    getattr(Mail, mail_function_to_be_triggered)(*args)

    logger.info(f"End > send_mail with function: {mail_function_to_be_triggered}")


@shared_task(
    name="import_items_via_csv",
    ignore_result=True,
    base=TransactionAwareTask
)
def import_items_via_csv(job_id, user_id):
    from .utils import Items

    Items.import_file(job_id, user_id)


@shared_task(
    name="update_stats_for_order",
    ignore_result=True,
    base=TransactionAwareTask
)
def update_stats_for_order(order_id):
    from .order.models import Order
    from .all_time_stat.models import AllTimeStat
    from .daily_stat.models import DailyStat
    from .menu_item.models import MenuItem

    # logger.info(f"Start > update_stats_for_order")

    order = Order.objects.get(id=order_id)
    if order.status == Constants.ORDER_STATUS_PENDING:
        customer = order.customer
        customer.update_stats_for(order)

        DailyStat.update_for(order)
        MenuItem.update_sales_count_for(order)

    venue = order.venue
    venue.update_stats_for(order)

    company = venue.company
    company.update_stats_for(order)
    AllTimeStat.update_for(order)

    if order.delivery_status == Constants.DELIVERY_STATUS_DELIVERED:
        driver = order.driver
        driver.update_stats_for_delivered_order(order)

    # logger.info(f"End > update_stats_for_order")


# This is triggered after accept button pressed by vendor
@shared_task(
    name="create_delivery_requests",
    ignore_result=True,
    base=TransactionAwareTask
)
def create_delivery_requests(order_id, max_distance=Api.LOWER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS):
    # If _create_delivery_requests returns True then stop further processing, else start looping
    if _create_delivery_requests(order_id, max_distance):
        # Schedule this task to run every 5 seconds, 5km from vendor
        # Setting this to every 2 seconds because it should try to get it to the driver as quickly as possible
        create_delivery_requests.apply_async(args=(order_id, Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS), countdown=2)


def _create_delivery_requests(order_id, max_distance):
    from .order.models import Order
    from .delivery_request.models import DeliveryRequest

    logger.info(f'Starting _create_delivery_requests for {order_id}')

    order = Order.objects.get(id=order_id)
    
    # If order is no longer looking for driver, then stop further processing
    if order.status != Constants.ORDER_STATUS_LOOKING_FOR_DRIVER:
        logger.info(f"Order {order_id} has been accepted. Stopping further delivery requests.")
        return False  # Stop further processing and scheduling if order is accepted by returning early

    # This is the important logic which is run each time
    delivery_requests = DeliveryRequest.create_for(order, max_distance)

    logger.info(f'Sending notification to new drivers {delivery_requests}')
    if delivery_requests:
        send_notification("send_delivery_requests", delivery_requests)
    
    return True

# This is triggered after a driver accepts the delivery request
# To stop the request from being accepted by multiple drivers
@shared_task(
    name="set_delivery_requests_as_missed",
    ignore_result=True,
    base=TransactionAwareTask
)
def set_delivery_requests_as_missed(order_id):
    from .delivery_request.models import DeliveryRequest

    # logger.info(f"Scheduled task started: update_delivery_requests_as_missedm {order_id}")
    # This doesn't set the active deliveryrequest as missed because that already has status accepted
    DeliveryRequest.objects.filter(order_id=order_id, status=Constants.DELIVERY_REQUEST_STATUS_PENDING).update(status=Constants.DELIVERY_REQUEST_STATUS_MISSED)

    logger.info(f"Scheduled task: update_delivery_requests_as_missed {order_id}")

# Beat schedule configuration
app.conf.beat_schedule = {
    'cancel-driver-not-found-or-expired-orders': {
        'task': 'cancel_driver_not_found_or_expired_orders',
        'schedule': crontab(minute='*/5'),  # Runs every 5 minutes
    },
}

def cancel_driver_not_found_or_expired_orders():
    from .order.models import Order
    from .delivery_request.models import DeliveryRequest
    from .all_time_stat.models import AllTimeStat
    from .utils import Constants, DateUtils

    logger.info(f"Periodic_task: cancel_driver_not_found_or_expired_orders")

    threshold = DateUtils.minutes_before(30)

    # FIRST CHECK FOR NO DRIVER FOUND ORDERS
    no_driver_found_orders = Order.objects.filter(status=Constants.ORDER_STATUS_LOOKING_FOR_DRIVER, started_looking_for_drivers_at__lte=threshold)

    for order in no_driver_found_orders:
        try:
            order.payment.refund()
        except Exception as e:
            logger.info(f"Failure while cancel_driver_not_found_or_expired_orders: {e}")
            continue
        logger.info(f"Automated task: Driver not found, Refunded order {order.id}")
        order.status = Constants.ORDER_STATUS_REJECTED
        order.rejection_reason = Constants.ORDER_REJECTION_REASON_NO_DRIVER_FOUND
        order.save()

        # Cancel all pending delivery requests
        order.delivery_requests.filter(
            status=Constants.DELIVERY_REQUEST_STATUS_PENDING
        ).update(
            status=Constants.DELIVERY_REQUEST_STATUS_EXPIRED
        )

    count_of_orders = no_driver_found_orders.count()

    if count_of_orders > 0:
        AllTimeStat.update(Constants.ALL_TIME_STAT_NO_DRIVER_FOUND_ORDER_COUNT, count_of_orders)

    # NOW CHECK FOR EXPIRED ORDERS
    expired_orders = Order.objects.filter(status=Constants.ORDER_STATUS_PENDING, created_at__lte=threshold)

    for order in expired_orders:
        try:
            order.payment.refund()
        except Exception as e:
            logger.info(f"Refund attempted for expired order but failed: {e}")
            continue
        logger.info(f"Automated task: Vendor did not accept, Refunded order {order.id}")
        order.status = Constants.ORDER_STATUS_REJECTED
        order.rejection_reason = Constants.ORDER_REJECTION_REASON_EXPIRED
        order.save()

    count_of_expired_orders = expired_orders.count()

    if count_of_expired_orders > 0:
        AllTimeStat.update(Constants.ALL_TIME_STAT_EXPIRED_ORDER_COUNT, count_of_expired_orders)

    # AND FINALLY set all pending delivery requests to missed for pending requests older than 30 minutes
    driver_missed_delivery_requests = DeliveryRequest.objects.filter(status=Constants.DELIVERY_REQUEST_STATUS_PENDING, created_at__lte=threshold)
    for delivery_request in driver_missed_delivery_requests:
        delivery_request.status = Constants.DELIVERY_REQUEST_STATUS_MISSED
        delivery_request.save()

@shared_task(
    name="send_notification",
    ignore_result=True,
    base=TransactionAwareTask
)
def send_notification(notification_function_to_be_triggered, *args):
    from .utils import Notification

    #logger.info(f"Start > send_notification with function: {notification_function_to_be_triggered}")

    getattr(Notification, notification_function_to_be_triggered)(*args)

    logger.info(f"Completed Queued Task: send_notification: {notification_function_to_be_triggered}")


@shared_task(
    name="generate_receipt_for_order",
    ignore_result=True,
    base=TransactionAwareTask
)
def generate_receipt_for_order(order_id):
    from .utils import Receipt
    from .order.models import Order
    import os

    if "CI" in os.environ and os.environ['CI'] == "true":
        return

    order = Order.objects.get(id=order_id)

    Receipt.generate(order)