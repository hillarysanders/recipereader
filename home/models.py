from __future__ import unicode_literals
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.utils.safestring import mark_safe


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
    ingredients_text = models.TextField(max_length=2048*2)
    instructions_text = models.TextField(max_length=2048*4)

    ingredients = models.TextField(max_length=2048*2, default='', blank=True, null=True)
    instructions = models.TextField(max_length=2048*4, default='', blank=True, null=True)
    # optional:
    prep_time_hours = models.IntegerField(blank=True, null=True, verbose_name='Prep time')
    prep_time_minutes = models.IntegerField(blank=True, null=True, verbose_name='')
    cook_time_hours = models.IntegerField(blank=True, null=True, verbose_name='Cook time')
    cook_time_minutes = models.IntegerField(blank=True, null=True, verbose_name='')
    ready_in_hours = models.IntegerField(blank=True, null=True, verbose_name='Ready in')
    ready_in_minutes = models.IntegerField(blank=True, null=True, verbose_name='')
    num_servings = models.IntegerField(blank=True, null=False, default=4)
    # your recipe image
    image = models.ImageField(blank=True, upload_to='images/recipes/', null=True)

    # invisible to the user stuff:
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    # # each recipe is related to a single user.
    # # on_delete=models.CASCADE means that if a user is deleted his / her recipes will be too.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.description

    # def save(self, *args, **kwargs):
    #     # todo fix this (not working atm)... Hm. maybe make into field? Or implement in view, or make into function?
    #     self.ingredients = mark_safe(self.ingredients_text.replace("\n", "<br/>"))
    #     self.instructions = mark_safe(self.instructions_text.replace("\n", "<br/>"))
    #     # todo put parsing info in a child class or somehting???
    #     super(Recipe, self).save(*args, **kwargs)

    def get_all_fields(self):
        """Returns a list of all field names on the instance."""
        fields = []
        for f in self._meta.fields:

            fname = f.name
            # resolve picklists/choices, with get_xyz_display() function
            get_choice = 'get_'+fname+'_display'
            if hasattr(self, get_choice):
                value = getattr(self, get_choice)()
            else:
                try :
                    value = getattr(self, fname)
                except AttributeError:
                    value = None

            # only display fields with values and skip some fields entirely
            if f.editable and value and f.name not in ('id',  'user', 'recipe_name',
                                                       'status', 'workshop', 'complete'):

                fields.append(
                  {
                   'label': f.verbose_name,
                   'name': f.name,
                   'value': value,
                  }
                )
        return fields

    def get_time(self, hours, minutes):
        if hours == 0 or hours is None:
            h = ''
        elif hours == 1:
            h = '1 h, '
        else:
            h = '{} h, '.format(hours)

        if minutes == 0 or minutes is None:
            m = ''
            h = h.replace(', ', '')
        elif minutes == 1:
            m = '1 m'
        else:
            m = '{} m'.format(minutes)

        line = h + m
        return line

    def get_prep_time(self):
        time = self.get_time(self.prep_time_hours, self.prep_time_minutes)
        time = '' if (time == '') else 'Prep Time: {}'.format(time)
        return time

    def get_cook_time(self):
        time = self.get_time(self.cook_time_hours, self.cook_time_minutes)
        time = '' if (time == '') else 'Cook Time: {}'.format(time)
        return time

    def get_ready_in_time(self):
        time = self.get_time(self.ready_in_hours, self.ready_in_minutes)
        time = '' if (time == '') else 'Ready In: {}'.format(time)
        return time


class ingredient_line(models.Model):
    raw_text = models.TextField(max_length=2048*2)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)


# making your own field type:
class IngredientField(models.Field):
    description = "An ingredient line and its parsing outputs"

    def __init__(self, *args, **kwargs):
        # do stuff ...
        super(IngredientField, self).__init__(*args, **kwargs)






