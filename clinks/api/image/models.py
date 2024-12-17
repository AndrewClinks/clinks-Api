from django.db import models

from ..utils.Models import SmartModel

from ..utils import File


class Image(SmartModel):

    id = models.AutoField(primary_key=True)

    thumbnail = models.CharField(max_length=255, null=True)
    banner = models.CharField(max_length=255, null=True)
    original = models.CharField(max_length=255)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Image: {}".format(self.id)

    def delete(self):
        File.delete(self.thumbnail)
        File.delete(self.banner)
        File.delete(self.original)
        self.hard_delete()






