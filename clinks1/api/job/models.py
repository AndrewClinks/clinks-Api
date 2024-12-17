from django.db import models

from ..image.models import Image
from ..category.models import Category

from ..utils.Models import SmartModel


class Job(SmartModel):

    id = models.AutoField(primary_key=True)

    data = models.TextField()

    errors = models.JSONField(null=True)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Job: {}".format(self.id)
