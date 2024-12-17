from django.db import models

from django.db.models import JSONField

from ..utils.Fields import EnumField
from ..utils.Models import SmartModel

from ..utils import Constants


class WebhookEvent(SmartModel):

    id = models.AutoField(primary_key=True)

    event_id = models.CharField(max_length=255)

    result = EnumField(options=Constants.WEBHOOK_EVENT_RESULTS)

    data = JSONField(null=True)

    ip = models.CharField(max_length=255)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "WebhookEvent: {}".format(self.id)





