from django.db import models
from django.contrib.gis.db.models import PointField

from ..utils.Models import SmartModel


class Address(SmartModel):

    id = models.AutoField(primary_key=True)

    line_1 = models.CharField(max_length=255)
    line_2 = models.CharField(max_length=255, null=True)
    line_3 = models.CharField(max_length=255, null=True)

    city = models.CharField(max_length=60)
    country = models.CharField(max_length=60)
    state = models.CharField(max_length=60)

    postal_code = models.CharField(max_length=20, null=True)
    country_short = models.CharField(max_length=5)

    point = PointField(srid=4326)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Address : {}".format(self.id)

    @staticmethod
    def create_or_update_for(instance, address_data):
        from .serializers import AddressCreateSerializer, AddressEditSerializer

        address = instance.address

        if address:
            serializer = AddressEditSerializer(instance=address, data=address_data)
            serializer.update(address, address_data)
            return

        serializer = AddressCreateSerializer(data=address_data)
        address = serializer.create(address_data)

        instance.address = address
        instance.save()
        return address

    def redact(self):
        from django.contrib.gis.geos import Point
        self.line_1 = "redacted_address_line_1"
        self.line_2 = None
        self.line_3 = None
        self.postal_code = None
        self.point = Point(53.3331671, -6.243948)
        self.save()