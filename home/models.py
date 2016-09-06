from __future__ import unicode_literals
from django.db import models


from django.contrib.auth.models import User
# Create your models here.
# Each model is represented by a class that subclasses django.db.models.Model. Each model has a number of class
# variables, each of which represents a database field in the model.
# Each field is represented by an instance of a Field class - e.g., CharField for character fields and DateTimeField
# for datetimes. This tells Django what type of data each field holds.


class Recipe(models.Model):
    # TextField is larger than CharField
    recipe_name = models.CharField(max_length=128, default='')
    description = models.CharField(max_length=1024)
    ingredients_text = models.TextField(max_length=2048)
    instructions_text = models.TextField(max_length=2048)
    # # optional positional first argument = field name:
    # pub_date = models.DateTimeField('date published')
    # # each recipe is related to a single user.
    # # on_delete=models.CASCADE means that if a user is deleted his / her recipes will be too.
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=User.objects.get_by_natural_key('hills'))

    def __str__(self):
        return self.description

    def get_all_fields(self):
        """Returns a list of all field names on the instance."""
        fields = []
        for f in self._meta.fields:

            fname = f.name
            # resolve picklists/choices, with get_xyz_display() function
            get_choice = 'get_'+fname+'_display'
            if hasattr( self, get_choice):
                value = getattr( self, get_choice)()
            else:
                try :
                    value = getattr(self, fname)
                except AttributeError:
                    value = None

            # only display fields with values and skip some fields entirely
            if f.editable and value and f.name not in ('id', 'status', 'workshop', 'user', 'complete', 'recipe_name'):

                fields.append(
                  {
                   'label': f.verbose_name,
                   'name': f.name,
                   'value': value,
                  }
                )
        return fields
