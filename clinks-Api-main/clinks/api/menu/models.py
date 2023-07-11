from django.db import models

from ..venue.models import Venue

from ..utils.Models import SmartModel


class Menu(SmartModel):
    venue = models.OneToOneField(Venue, primary_key=True, related_name="menu", on_delete=models.CASCADE)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Menu {}: ".format(self.venue.id)
