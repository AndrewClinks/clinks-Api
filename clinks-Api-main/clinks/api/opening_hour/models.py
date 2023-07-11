
from django.db import models

from ..utils import Constants

from ..venue.models import Venue

from ..utils.Fields import EnumField
from ..utils.Models import SmartModel
from ..utils import List


class OpeningHour(SmartModel):

    id = models.AutoField(primary_key=True)

    venue = models.ForeignKey(Venue, related_name="opening_hours", on_delete=models.CASCADE)

    day = EnumField(options=Constants.DAYS)

    order = models.PositiveIntegerField()

    starts_at = models.TimeField()

    ends_at = models.TimeField()

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "OpeningHour: {}".format(self.id)

    @staticmethod
    def get_ordered_by_date(hours):
        days = Constants.DAYS_ORDERED

        ordered = []

        for day in days:
            hour = List.find(hours, "day", day)

            if hour:
                ordered.append(hour)

        return ordered
