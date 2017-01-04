# Register your models here.
from django.contrib import admin
from .models import Recipe, UserProxy
# Register your models here.


# We need to tell the admin that Question objects should have an admin interface:
# this class isn't required, it just allows you to order your fields in the admin site interface:
class RecipeAdmin(admin.ModelAdmin):
    fields = ('recipe_name', 'description', 'user_proxy', 'ingredients_text', 'instructions_text',
              'num_servings', 'image')
    list_display = ('recipe_name', 'description', 'ingredients_text', 'user_proxy')

    # this adds a search box to the top of the admin/polls/question page, so you can search for question text:
    search_fields = ['recipe_name', 'description']

# this does the registering:
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(UserProxy)
