from django.conf.urls import url

from . import views

app_name = 'home'
urlpatterns = [
    # match to ''
    # ex: /polls/
    url(r'^$', views.auth_login, name='login'),
    url(r'^home/$', views.index, name='index'),
    url(r'^welcome/$', views.welcome, name='welcome'),
    url(r'^logout/$', views.logout_user, name='logout_user'),
    url(r'^recipes/add/$', views.add_recipe, name='add_recipe'),
    url(r'^recipes/detail/(?P<pk>[0-9]+)/$', views.recipe_detail, name='recipe_detail'),
    url(r'^recipes/delete/(?P<pk>[0-9]+)/$', views.delete_recipe, name='delete_recipe'),
    url(r'^recipes/edit/(?P<pk>[0-9]+)/$', views.edit_recipe, name='edit_recipe'),
    url(r'^cookbook/$', views.cookbook, name='cookbook'),
    url(r'^about/$', views.about, name='about'),
    url(r'^profile/$', views.profile, name='profile'),
]
