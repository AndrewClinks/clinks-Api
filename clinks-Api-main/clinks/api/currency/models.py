from django.db import models

from ..utils.Models import SmartModel


class Currency(SmartModel):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=40)
    symbol = models.CharField(max_length=2)

    code = models.CharField(max_length=5)
    iso_code = models.CharField(max_length=10)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Currency: {}".format(self.name)

