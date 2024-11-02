from celery.schedules import crontab
from celery.task import periodic_task, Task
from celery import task
from celery.utils.log import get_task_logger
from celery import shared_task
from django.db import transaction

from .utils import Constants, Api


from .utils import Mail

logger = get_task_logger(__name__)


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
    if not _create_delivery_requests(order_id, max_distance):
        # Schedule this task to run every 5 seconds, 5km from vendor
        # Setting this to every 2 seconds because it should try to get it to the driver as quickly as possible
        create_delivery_requests.apply_async(args=(order_id, Api.UPPER_MAX_DRIVER_DISTANCE_TO_VENUE_IN_KMS), countdown=2)


def _create_delivery_requests(order_id, max_distance):
    from .order.models import Order
    from .delivery_request.models import DeliveryRequest

    logger.info(f'Starting _create_delivery_requests for {order_id}')

    order = Order.objects.get(id=order_id)
    
    # Check if the order is already accepted, and if so, do not continue
    if order.status == Constants.ORDER_STATUS_ACCEPTED:
        logger.info(f"Order {order_id} has been accepted. Stopping further delivery requests.")
        return False  # Stop further processing and scheduling if order is accepted by returning early

    # This is the important logic which is run each time
    delivery_requests = DeliveryRequest.create_for(order, max_distance)

    logger.info(f'Sending notification to drivers {delivery_requests}')
    if delivery_requests:
        send_notification("send_delivery_requests", delivery_requests)
    
    return True

# This is triggered after the driver accepts the delivery request
@shared_task(
    name="set_delivery_requests_as_missed",
    ignore_result=True,
    base=TransactionAwareTask
)
def set_delivery_requests_as_missed(order_id):
    from .delivery_request.models import DeliveryRequest

    # logger.info(f"Scheduled task started: update_delivery_requests_as_missedm {order_id}")

    DeliveryRequest.objects.filter(order_id=order_id, status=Constants.DELIVERY_REQUEST_STATUS_PENDING).update(status=Constants.DELIVERY_REQUEST_STATUS_MISSED)

    logger.info(f"Scheduled task: update_delivery_requests_as_missed {order_id}")


@periodic_task(
    run_every=(crontab(minute='*/5')),
    name="cancel_driver_not_found_or_expired_orders",
    ignore_result=True
)
def cancel_driver_not_found_or_expired_orders():
    from .order.models import Order
    from .all_time_stat.models import AllTimeStat
    from .utils import Constants, DateUtils

    logger.info(f"Periodic_task: cancel_driver_not_found_or_expired_orders")

    threshold = DateUtils.minutes_before(30)

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

        order.delivery_requests.filter(status=Constants.DELIVERY_REQUEST_STATUS_PENDING).update(status=Constants.DELIVERY_REQUEST_STATUS_EXPIRED)

    count_of_orders = no_driver_found_orders.count()

    if count_of_orders > 0:
        AllTimeStat.update(Constants.ALL_TIME_STAT_NO_DRIVER_FOUND_ORDER_COUNT, count_of_orders)

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

    # logger.info(f"End > cancel_driver_not_found_or_expired_orders")


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