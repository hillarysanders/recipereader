from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        exclude = ["password1", "password2"]

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        for key in ["first_name", "last_name", "email"]:
            self.fields[key].required = False

        self.fields['username'].help_text = ''
        self.fields['password2'].help_text = ''


class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "password"]

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = ''

# sweet. now make a welcome page, and better error catching, and a login along with create user form.
# and figure out where the users are going in the database, and make it all pretty.

# ok, awesome. now on the home page show your user profile name in the corner. and add a container box.
# and also figure out how to inherit web pages with django.