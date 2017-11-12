"""ebdjango URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # the url() function has four arguments:
    # - regex: Django starts at the first regular expression and makes its way down the list, comparing the requested
    # URL against each regular expression until it finds one that matches.
    # - view: When Django finds a regular expression match, Django calls the specified view function, with an
    # HttpRequest object as the first argument and any "captured" values from the regular expression as other
    # arguments. If the regex uses simple captures, values are passed as positional arguments; if it uses named
    # captures, values are passed as keyword arguments.
    # - kwargs: Arbitrary keyword arguments can be passed in a dictionary to the target view.
    # - name: Naming your URL lets you refer to it unambiguously from elsewhere in Django, especially from within
    # templates.

    # include URLs from polls/urls.py
    url(r'^polls/', include('polls.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^', include('home.urls')),
]