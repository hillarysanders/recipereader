from django.conf.urls import url

from . import views

app_name = 'home'
urlpatterns = [
    # match to ''
    # ex: /polls/
    url(r'^$', views.auth_login, name='login'),
    url(r'^home/$', views.index, name='index')

]
