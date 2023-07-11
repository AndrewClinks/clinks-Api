from django.db import models

from ..user.models import User

from ..utils.Fields import EnumField
from ..utils import Constants

from ..utils.Models import SmartModel


class Admin(SmartModel):

    user = models.OneToOneField(User, primary_key=True, related_name='admin',  on_delete=models.CASCADE)

    role = EnumField(options=Constants.ADMIN_ROLES, default=Constants.ADMIN_ROLE_DEFAULT)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "Admin {}: ".format(self.user.id)