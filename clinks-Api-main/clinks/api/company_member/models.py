from django.db import models

from ..user.models import User
from ..company.models import Company
from ..venue.models import Venue

from ..utils.Fields import EnumField
from ..utils import Constants

from ..utils.Models import SmartModel


class CompanyMember(SmartModel):

    user = models.OneToOneField(User, primary_key=True, related_name='company_member',  on_delete=models.CASCADE)

    role = EnumField(options=Constants.COMPANY_MEMBER_ROLES, default=Constants.COMPANY_MEMBER_ROLE_DEFAULT)

    company = models.ForeignKey(Company, related_name="members", on_delete=models.CASCADE)

    active_venue = models.ForeignKey(Venue, related_name="active_members", null=True, on_delete=models.SET_NULL)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Company Member {}: ".format(self.user.id)