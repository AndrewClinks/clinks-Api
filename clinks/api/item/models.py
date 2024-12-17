from django.db import models

from ..image.models import Image
from ..category.models import Category

from ..utils.Models import SmartModel


class Item(SmartModel):

    id = models.AutoField(primary_key=True)

    title = models.CharField(max_length=255)

    image = models.OneToOneField(Image, related_name="item", on_delete=models.CASCADE)

    subcategory = models.ForeignKey(Category, related_name="items", on_delete=models.CASCADE)

    description = models.TextField(null=True)

    menu_item_count = models.PositiveIntegerField(default=0)

    sales_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Item: {}".format(self.id)

    @staticmethod
    def update_item_count_for(subcategory):
        subcategory.item_count = Item.objects.filter(subcategory=subcategory).count()
        subcategory.save()

        category = subcategory.parent
        category.item_count = Item.objects.filter(subcategory__parent_id=subcategory.parent_id).count()
        category.save()
