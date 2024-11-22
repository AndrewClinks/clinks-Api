from django.db import models

from ..utils.Fields import EnumField
from ..utils.Models import SmartModel

from django.contrib.gis.db.models import PointField

from ..utils import Constants, Log

import logging
logger = logging.getLogger('clinks-api-live')

class DeliveryRequest(SmartModel):
    id = models.AutoField(primary_key=True)

    driver = models.ForeignKey("api.Driver", related_name="delivery_requests", on_delete=models.CASCADE)

    order = models.ForeignKey("api.Order", related_name="delivery_requests", on_delete=models.CASCADE)

    status = EnumField(options=Constants.DELIVERY_REQUEST_STATUSES)

    driver_location = PointField(srid=4326)

    accepted_at = models.DateTimeField(null=True)

    rejected_at = models.DateTimeField(null=True)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return f"DeliveryRequest: id: {self.id}, driver: {self.driver}"

    # Called by the celery scheduled task create_delivery_requests
    @staticmethod
    def create_for(order, max_distance):
        from ..utils import Nearby, Exception
        from ..driver.models import Driver
        from django.db.models import Q
        from rest_framework import status

        if order.status != Constants.ORDER_STATUS_LOOKING_FOR_DRIVER:
            raise Exception.raiseError(f"This order: {order.id} isn't looking for drivers", status_code=status.HTTP_400_BAD_REQUEST)

        queryset = Driver.objects.filter(current_delivery_request__isnull=True)

        queryset = queryset.exclude(delivery_requests__order=order).distinct()
        # Log.create(f"Available drivers for order {order.id}: {queryset}")

        nearby_drivers = Nearby.drivers(queryset, order, max_distance=max_distance).distinct()
        Log.create(f"Nearby drivers for order {order.id}: {nearby_drivers}")

        delivery_requests = []

        if nearby_drivers:
            for driver in nearby_drivers:
                # Make sure the driver does not have an existing delivery request already
                existing_request = DeliveryRequest.objects.filter(
                    driver=driver,
                    order=order,
                    status=Constants.DELIVERY_REQUEST_STATUS_PENDING
                ).exists()
                if not existing_request:
                    delivery_requests.append(DeliveryRequest(
                        driver=driver,
                        order=order,
                        status=Constants.DELIVERY_REQUEST_STATUS_PENDING,
                        driver_location=driver.last_known_location
                    ))

            delivery_requests = DeliveryRequest.objects.bulk_create(delivery_requests)
            logger.info(f"Created delivery requests for order {order.id}: {delivery_requests}")
        else:
            logger.info(f"No nearby drivers found for order {order.id}")
        
        return delivery_requests


