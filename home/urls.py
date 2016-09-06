from django.conf.urls import url

from . import views

app_name = 'home'
urlpatterns = [
    # match to ''
    # ex: /polls/
    url(r'^$', views.auth_login, name='login'),
    url(r'^home/$', views.index, name='index'),
    url(r'^recipes/add/$', views.add_recipe, name='add_recipe'),
    url(r'^recipes/detail/(?P<pk>[0-9]+)/$', views.RecipeDetailView.as_view(), name='recipe_detail')
]
