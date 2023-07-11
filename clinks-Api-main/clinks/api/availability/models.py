from django.db import models

from ..utils import Constants

from ..utils.Fields import EnumField

from ..utils.Models import SmartModel


class Availability(SmartModel):

    id = models.AutoField(primary_key=True)

    day = EnumField(options=Constants.DAYS)

    starts_at = models.TimeField(null=True)

    ends_at = models.TimeField(null=True)

    closed = models.BooleanField(default=False)

    date = models.DateField(null=True)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Availability: {}".format(self.id)







