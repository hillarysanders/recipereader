from autocomplete_light import shortcuts as al
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Recipe


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2", "first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        for key in ["first_name", "last_name", "email"]:
            self.fields[key].required = False

        self.fields['username'].help_text = ''
        self.fields['password2'].help_text = ''

        self.fields['username'].widget = forms.TextInput(attrs={'placeholder': ''})
        self.fields['password1'].widget = forms.TextInput(attrs={'placeholder': '', 'type': 'password'})
        self.fields['password2'].widget = forms.TextInput(attrs={'placeholder': '', 'type': 'password'})
        self.fields['first_name'].widget = forms.TextInput(attrs={'placeholder': '(optional)'})
        self.fields['last_name'].widget = forms.TextInput(attrs={'placeholder': '(optional)'})
        self.fields['email'].widget = forms.TextInput(attrs={'placeholder': '(optional)'})


class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "password"]

    def add_prefix(self, field_name):
        # this is a hack to make sure form field IDs don't clash in the login page -
        # there's a username, password for login and make-new-user forms, so if we use the default
        # names the IDs clash, which is bad.
        # http://stackoverflow.com/questions/8801910/override-django-form-fields-name-attr
        field_name = 'login_{}'.format(field_name)
        return super(LoginForm, self).add_prefix(field_name)

    def __init__(self, *args, **kwargs):
        # first call the 'real' __init__()
        super(LoginForm, self).__init__(*args, **kwargs)
        # then do extra stuff:
        self.fields['username'].help_text = ''
        self.fields['username'].widget = forms.TextInput(attrs={'placeholder': ''})
        self.fields['password'].widget = forms.PasswordInput(attrs={'placeholder': ''})


class AddRecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        autocomplete_fields = ("tags")
        fields = '__all__'
        exclude = ('user_proxy', 'pub_date', 'ingredients', 'instructions',
                   'slug', 'bw_pngs', 'ingredients_sans_amounts')
        widgets = {
           "tags": al.TextWidget("RecipeTagsAutocomplete"),
        }

    def __init__(self, *args, **kwargs):
        super(AddRecipeForm, self).__init__(*args, **kwargs)

        for f in ['prep_time_hours', 'cook_time_hours', 'ready_in_hours']:
            self.fields[f].widget = forms.NumberInput(attrs={'placeholder': 'hours'})
        for f in ['prep_time_minutes', 'cook_time_minutes', 'ready_in_minutes']:
            self.fields[f].widget = forms.NumberInput(attrs={'placeholder': 'minutes'})

        self.fields['ingredients_text'].widget = forms.Textarea(attrs={
            'placeholder': '(required)'
        })
        self.fields['instructions_text'].widget = forms.Textarea(attrs={
            'placeholder': '(required)'
        })

        # make recipe name big:
        self.fields['recipe_name'].widget = forms.TextInput(attrs={'style': 'font-size: 30px'})

