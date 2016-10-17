from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.urls import reverse
from django.db.models.fields.related import ManyToManyField
from django.template.defaultfilters import slugify
from . import conversions
from .utils import Timer
# Create your models here.
# Each model is represented by a class that subclasses django.db.models.Model. Each model has a number of class
# variables, each of which represents a database field in the model.
# Each field is represented by an instance of a Field class - e.g., CharField for character fields and DateTimeField
# for datetimes. This tells Django what type of data each field holds.


# create session id object to be used only when a user tries to record a recipe but is not logged in.
# looking in e.g. cookbook will use userproxy object instead of user object.
# then if they create a user account, the UserProxy instance will be modified to link to a user,
# instead of None.
# at some point set it so e.g. if a cookie has become inactive (how long is this?) you delete the UserProxy instance
# (and therefore, its recipes) if there is no attached user account.

class UserProxy(models.Model):
    """
    User proxy model to help enable anonymous browsing
    When a user registers, create an instance of this.
    session will = a cookie session, i.e. request.session.session_key

    session is basically data stored on your server that is identified by a session id sent as a cookie to the browser.
    The browser will send the cookie back containing the session id on all subsequent requests either until the
    browser is closed or the cookie expires (depending on the expires value that is sent with the cookie header,
    which you can control from Django with set_expiry
    """
    # if a user is logged in, their user = the user. Else, None.
    user = models.ForeignKey(User, null=True, blank=True, default=None)
    # if a user is logged in, their session = None. Else, request.session.session_key.
    session = models.CharField(max_length=40, blank=True, default='')

    def __str__(self):
        if self.user:
            return str(self.user.username)
        else:
            return 'anonymously browsing\n\tsession: {}'.format(self.session)


class Recipe(models.Model):
    # TextField is larger than CharField
    recipe_name = models.CharField(max_length=128, default='')
    description = models.CharField(max_length=1024, default='')
    ingredients_text = models.TextField(max_length=2048*2, verbose_name='Ingredients')
    instructions_text = models.TextField(max_length=2048*4, verbose_name='Instructions')
    ingredients = JSONField(default=dict)
    instructions = JSONField(default=dict)

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
    slug = models.SlugField(max_length=40, default='default-slug')
    public = models.BooleanField(default=True, verbose_name='make recipe public?')

    # invisible to the user stuff:
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    # # each recipe is related to a single user.
    # # on_delete=models.CASCADE means that if a user is deleted his / her recipes will be too.
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_proxy = models.ForeignKey(UserProxy, on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        # parse ingredients and instructions:
        with Timer(name='Parsing ingredients') as t1:
            self.ingredients = conversions.parse_ingredients(self.ingredients_text)

        with Timer('Parsing instructions') as t2:
            self.instructions = conversions.parse_ingredients(self.instructions_text)

        self.slug = slugify(self.recipe_name[:40])

        super(Recipe, self).save(*args, **kwargs)

    def __str__(self):
        return self.description

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    def get_absolute_url(self):
        return ('recipe', (), {
            'slug': self.slug,
            'pd': self.pk,
        })

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
        # ugly structure since originally did 'minutes' vs 'minute'.
        if hours == 0 or hours is None:
            h = ''
        elif hours == 1:
            h = '1 h, '
        else:
            h = '{} h, '.format(hours)

        # the or (minutes*60 == hours) is in case people think they have to put in e.g. .5 hours and 30 minutes?
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


# class NumberMatch(models.Model):
#     start = models.IntegerField()
#     end = models.IntegerField()
#     pattern = models.CharField()
#     replacement = models.CharField()
#     value = models.FloatField()
#     ingredient_line = models.ForeignKey(IngredientLine, on_delete=models.CASCADE)

#
# class IngredientLine(models.Model):
#     raw_text = models.TextField(max_length=2048*2, blank=False, null=False)
#     recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
#     # todo add in more fields that are created upon save, based on conversion text parsing of raw_text.
#
#     def save(self, *args, **kwargs):
#         # if self.raw_text:
#         #     # make attributes that are the output of parsing the line:
#         #     parsed = conversions.parse_ingredient_line(self.raw_text)
#         #     # todo this doesn't work still:
#         #     self.new_text = parsed['parsed_line']
#
#         super(IngredientLine, self).save(*args, **kwargs)
#
#         # TODO would using postgres mean we could use multiple fields in django?

# class IngredientNumber(models.Model):
#     start = models.IntegerField()
#     end = models.IntegerField()
#     pattern = models.CharField()
#     number_name = models.CharField()
#     number_value = models.FloatField()
#     ingredient_line = models.ForeignKey(IngredientLine)






