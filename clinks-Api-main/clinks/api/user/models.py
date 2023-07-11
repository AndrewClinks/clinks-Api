from django.db import models
from django.contrib.auth.models import AbstractBaseUser

from ..user.managers import UserManager

from ..utils import Constants, DateUtils
import uuid
from ..utils.Fields import EnumField


class User(AbstractBaseUser):
    """This class represents the user model"""

    REQUIRED_FIELDS = ('role', 'first_name', 'last_name')
    USERNAME_FIELD = 'email'

    is_anonymous = False
    is_authenticated = True

    objects = UserManager()

    id = models.AutoField(primary_key=True)
    role = EnumField(options=Constants.USER_ROLES)

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)

    password = models.CharField(max_length=255)

    verification_code = models.CharField(max_length=5, null=True)

    status = EnumField(options=Constants.USER_STATUSES, default=Constants.USER_STATUS_DEFAULT)

    active = models.BooleanField(default=True)

    last_seen = models.DateTimeField(auto_now=True)

    phone_country_code = models.CharField(max_length=255, null=True)
    phone_number = models.CharField(max_length=255, null=True)

    email_verified = models.BooleanField(default=False)

    date_of_birth = models.DateField(null=True)

    deleted_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "User: {}".format(self.id)

    def soft_delete(self):
        from ..utils import DateUtils
        self.status = Constants.USER_STATUS_SUSPENDED
        self.active = False
        self.deleted_at = DateUtils.now()
        self.save()

    def redact(self):
        self.first_name = "deleted"
        self.last_name = "user"
        self.email = f"deleted{uuid.uuid4()}@user.ie"
        self.status = Constants.USER_STATUS_DELETED
        self.deleted_at = DateUtils.now()

        self.phone_number = None
        self.phone_country_code = None
        self.active = False

        self.save()
