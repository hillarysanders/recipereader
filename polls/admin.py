from django.contrib import admin
from .models import Choice, Question
# Register your models here.


# note the class that ChoiceInline inherits from. admin.TabularInline makes a more succinct,
# tabular format, while admin.StackedInline makes a stacked format.
class ChoiceInline(admin.TabularInline):
    model = Choice
    # by default offer two choices:
    extra = 2


# We need to tell the admin that Question objects should have an admin interface:
# this class isn't required, it just allows you to order your fields in the admin site interface:
class QuestionAdmin(admin.ModelAdmin):
    # fields = ['pub_date', 'question_text']
    fieldsets = [
        (None,               {'fields': ['question_text']}),
        ('Date information', {'fields': ['pub_date']}),
    ]
    # This tells Django: "Choice objects are edited on the Question admin page"
    inlines = [ChoiceInline]
    # this tells django what to show when describing a question object (optional, default is just __str__):
    list_display = ('question_text', 'pub_date', 'was_published_recently')
    # this adds a search box to the top of the admin/polls/question page, so you can search for question text:
    search_fields = ['question_text']



# this does the registering:
admin.site.register(Question, QuestionAdmin)

