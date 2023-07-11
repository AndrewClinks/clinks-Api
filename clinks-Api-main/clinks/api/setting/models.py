from django.db import models

from ..image.models import Image

from ..utils.Models import SmartModel

from ..utils import Constants
from ..utils.Fields import EnumField


class Setting(SmartModel):

    id = models.AutoField(primary_key=True)

    key = EnumField(options=Constants.SETTING_KEYS)

    value = models.CharField(max_length=255)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return f"Setting: {self.key} : {self.value}"

    @staticmethod
    def get_minimum_age():
        minimum_age = Setting.objects.filter(key=Constants.SETTING_KEY_MINIMUM_AGE).first().value
        return int(minimum_age)

    @staticmethod
    def get_minimum_order_amount():
        minimum_age = Setting.objects.filter(key=Constants.SETTING_KEY_MINIMUM_ORDER_AMOUNT).first()
        if not minimum_age:
            return None
        return int(minimum_age.value)

    @staticmethod
    def update(key, value):
        setting, created = Setting.objects.update_or_create(key=key, defaults={"key": key, "value": value})
        return setting
