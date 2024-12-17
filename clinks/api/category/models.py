from django.db import models

from ..utils.Models import SmartModel
from ..image.models import Image


class Category(SmartModel):

    id = models.AutoField(primary_key=True)

    title = models.CharField(max_length=255)

    parent = models.ForeignKey("self", related_name="children",  null=True, on_delete=models.CASCADE)

    image = models.OneToOneField(Image, related_name="category", on_delete=models.CASCADE)

    sales_count = models.PositiveIntegerField(default=0)

    menu_item_count = models.PositiveIntegerField(default=0)

    item_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return f"Category: {self.id}"
