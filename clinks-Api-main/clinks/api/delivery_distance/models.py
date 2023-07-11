from django.db import models

from ..utils.Models import SmartModel


class DeliveryDistance(SmartModel):

    id = models.AutoField(primary_key=True)

    starts = models.DecimalField(max_digits=10, decimal_places=2)

    ends = models.DecimalField(max_digits=10, decimal_places=2)

    fee = models.PositiveIntegerField()

    driver_fee = models.PositiveIntegerField()

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "DeliveryDistance {}: ".format(self.id)

    @staticmethod
    def max_delivery_distance():
        return DeliveryDistance.objects.order_by("-ends").first().ends

    @staticmethod
    def get_by_distance(distance, raise_exception_on_not_found=True):
        if distance == 0:
            delivery_distance = DeliveryDistance.objects.filter(starts=distance).first()
        else:
            delivery_distance = DeliveryDistance.objects.filter(starts__lt=distance, ends__gte=distance).first()

        if not delivery_distance and raise_exception_on_not_found:
            raise Exception("Delivery fee for this distance is not found")

        return delivery_distance


