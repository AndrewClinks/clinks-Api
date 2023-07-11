from django.db import models

from ..menu.models import Menu
from ..category.models import Category

from ..utils.Models import SmartModel


class MenuCategory(SmartModel):

    id = models.AutoField(primary_key=True)

    menu = models.ForeignKey(Menu, related_name="categories", on_delete=models.CASCADE)

    category = models.ForeignKey(Category, related_name="menu_categories", on_delete=models.CASCADE)

    order = models.PositiveIntegerField()

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "MenuCategory {}: ".format(self.id)
