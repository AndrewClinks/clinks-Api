from django.db import models

from ..utils.Fields import EnumField

from ..user.models import User
from ..utils import Constants

from ..utils.Models import SmartModel


class Log(SmartModel):

    id = models.AutoField(primary_key=True)

    type = EnumField(options=Constants.LOG_TYPES)

    user = models.ForeignKey(User, related_name="logs", on_delete=models.CASCADE)

    request_data = models.JSONField(null=True)

    request_url = models.CharField(max_length=255)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Log : {}".format(self.id)
