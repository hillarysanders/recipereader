from django.conf.urls import url

from . import views

app_name = 'home'
urlpatterns = [
    # match to ''
    # ex: /polls/
    url(r'^$', views.welcome, name='welcome'),
    url(r'^home/$', views.index, name='index'),
    url(r'^login/$', views.auth_login, name='login'),
    url(r'^logout/$', views.logout_user, name='logout_user'),
    url(r'^recipes/add/$', views.add_recipe, name='add_recipe'),
    url(r'^recipes/detail/(?P<slug>[-\w\d]+),(?P<pk>\d+)/$', views.recipe_detail, name='recipe_detail'),
    url(r'^recipes/delete/(?P<pk>[0-9]+)/$', views.delete_recipe, name='delete_recipe'),
    url(r'^recipes/edit/(?P<slug>[-\w\d]+),(?P<pk>\d+)/$', views.edit_recipe, name='edit_recipe'),
    url(r'^recipes/ruh-roh/$', views.bad_perm, name='bad_perm'),
    url(r'^cookbook/$', views.cookbook, name='cookbook'),
    url(r'^about/$', views.about, name='about'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^public_profile/(?P<username>[+-@_.\w]+)$', views.public_profile, name='public_profile'),
    # ajax stuff:
    url(r'^ajax/change_units/$', views.ajax_change_units, name='ajax_change_units'),
    url(r'^ajax/change_servings/$', views.ajax_change_servings, name='ajax_change_servings'),
    url(r'^ajax/add_recipe_to_stash/$', views.ajax_add_recipe_to_stash, name='ajax_add_recipe_to_stash'),
    url(r'^ajax/validate_username/$', views.ajax_validate_username, name='ajax_validate_username'),
]
