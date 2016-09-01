from django.contrib import admin
from .models import Question

# Register your models here.

# We need to tell the admin that Question objects should have an admin interface:
admin.site.register(Question)
