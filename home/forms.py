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
        self.fields['first_name'].widget = forms.TextInput(attrs={'placeholder': '(optional)'})
        self.fields['last_name'].widget = forms.TextInput(attrs={'placeholder': '(optional)'})
        self.fields['email'].widget = forms.TextInput(attrs={'placeholder': '(optional)'})


class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "password"]

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = ''


class AddRecipe(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'
        exclude = ('user', 'pub_date',)

    def __init__(self, *args, **kwargs):
        super(AddRecipe, self).__init__(*args, **kwargs)

        self.fields['description'].widget = forms.TextInput(attrs={'size': '200'})
        self.fields['ingredients_text'].widget = forms.Textarea(attrs={'class': "big_form_input"})
        self.fields['instructions_text'].widget = forms.Textarea(attrs={'class': "big_form_input"})







# sweet. now make a welcome page, and better error catching, and a login along with create user form.
# and figure out where the users are going in the database, and make it all pretty.

# ok, awesome. now on the home page show your user profile name in the corner. and add a container box.
# and also figure out how to inherit web pages with django.

# yahoo, done! OK, now add an add recipe page! Fix all the add_recipe stuff :). Model after polls?