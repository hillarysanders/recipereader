from __future__ import unicode_literals
import datetime
from django.utils import timezone
from django.db import models
# Create your models here.

# Each model is represented by a class that subclasses django.db.models.Model. Each model has a number of class
# variables, each of which represents a database field in the model.
# Each field is represented by an instance of a Field class - e.g., CharField for character fields and DateTimeField
# for datetimes. This tells Django what type of data each field holds.


class User(models.Model):
    username = models.CharField(max_length=200)
    # optional positional first argument = field name:
    start_date = models.DateTimeField('start date')

    def __str__(self):
        return self.username

    def new_user(self):
        return self.start_date >= timezone.now() - datetime.timedelta(days=30)


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


