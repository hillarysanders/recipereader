from __future__ import unicode_literals
import datetime
from django.utils import timezone
from django.db import models


# from django.contrib.auth.models import PermissionsMixin
# from django.contrib.auth.base_user import AbstractBaseUser
# from django.utils.translation import ugettext_lazy as _
# from django.contrib.auth.models import UserManager
# from django.core.mail import send_mail
# from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
# from django.utils import six

from django.contrib.auth.models import User
# Create your models here.
# Each model is represented by a class that subclasses django.db.models.Model. Each model has a number of class
# variables, each of which represents a database field in the model.
# Each field is represented by an instance of a Field class - e.g., CharField for character fields and DateTimeField
# for datetimes. This tells Django what type of data each field holds.


# class User(models.Model):
#     username = models.CharField(max_length=100)
#     # optional positional first argument = field name:
#     start_date = models.DateTimeField('start date')
#     first_name = models.CharField(max_length=50)
#     last_name = models.CharField(max_length=50)
#     email = models.CharField(max_length=100)
#     foo = 'bar'
#
#     def __str__(self):
#         return self.username
#
#     def new_user(self):
#         return self.start_date >= timezone.now() - datetime.timedelta(days=30)
#

class Recipe(models.Model):
    # TextField is larger than CharField
    description = models.CharField(max_length=1024)
    ingredients_text = models.TextField()
    instructions_text = models.TextField()
    # optional positional first argument = field name:
    pub_date = models.DateTimeField('date published')
    # each recipe is related to a single user.
    # on_delete=models.CASCADE means that if a user is deleted his / her recipes will be too.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.description


# class User(AbstractBaseUser, PermissionsMixin):
#     """
#     An abstract base class implementing a fully featured User model with
#     admin-compliant permissions.
#
#     Username and password are required. Other fields are optional.
#     """
#     username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()
#
#     username = models.CharField(
#         _('username'),
#         max_length=150,
#         unique=True,
#         help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
#         validators=[username_validator],
#         error_messages={
#             'unique': _("A user with that username already exists."),
#         },
#     )
#     first_name = models.CharField(_('first name'), max_length=30, blank=True, unique=False)
#     last_name = models.CharField(_('last name'), max_length=30, blank=True, unique=False)
#     email = models.EmailField(_('email address'), max_length=150, blank=True, unique=False)
#     is_staff = models.BooleanField(
#         _('staff status'),
#         default=False,
#         help_text=_('Designates whether the user can log into this admin site.'),
#     )
#     is_active = models.BooleanField(
#         _('active'),
#         default=True,
#         help_text=_(
#             'Designates whether this user should be treated as active. '
#             'Unselect this instead of deleting accounts.'
#         ),
#     )
#     date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
#
#     objects = UserManager()
#
#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = ['username']
#
#     class Meta:
#         verbose_name = _('user')
#         verbose_name_plural = _('users')
#         abstract = True
#
#     def get_full_name(self):
#         """
#         Returns the first_name plus the last_name, with a space in between.
#         """
#         full_name = '%s %s' % (self.first_name, self.last_name)
#         return full_name.strip()
#
#     def get_short_name(self):
#         "Returns the short name for the user."
#         return self.first_name
#
#     def email_user(self, subject, message, from_email=None, **kwargs):
#         """
#         Sends an email to this User.
#         """
#         send_mail(subject, message, from_email, [self.email], **kwargs)