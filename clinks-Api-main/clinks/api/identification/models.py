from django.db import models

from ..image.models import Image

from ..utils.Models import SmartModel

from ..utils import Constants
from ..utils.Fields import EnumField


class Identification(SmartModel):

    id = models.AutoField(primary_key=True)

    front = models.OneToOneField(Image, related_name="front", on_delete=models.CASCADE)

    back = models.OneToOneField(Image, related_name="back", null=True, on_delete=models.SET_NULL)

    type = EnumField(options=Constants.IDENTIFICATION_TYPES)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Identification {}: ".format(self.id)

    def delete(self):
        self.front.delete()
        self.back.delete()
        self.hard_delete()

