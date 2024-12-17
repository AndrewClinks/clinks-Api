from django.db import models

from ..company_member.models import CompanyMember
from ..venue.models import Venue

from ..utils.Models import SmartModel


class Staff(SmartModel):

    id = models.AutoField(primary_key=True)

    company_member = models.ForeignKey(CompanyMember, related_name="staff", on_delete=models.CASCADE)

    venue = models.ForeignKey(Venue, related_name="staff", on_delete=models.CASCADE)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Staff: {}".format(self.id)
