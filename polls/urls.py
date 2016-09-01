from django.conf.urls import url

from . import views

app_name = 'polls'
urlpatterns = [
    # match to ''
    # ex: /polls/
    url(r'^$', views.index, name='index', kwargs=dict(a=10, b=20, c=30)),
    # ex: /polls/5/
    # note how the pk (primary key) argument is named. The value will be passed to views.detail(), which has
    # the named argument question_id. Pretty cool.
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # ex: /polls/5/results/
    url(r'^(?P<pk>[0-9]+)/results/$', views.ResultsView.as_view(), name='results'),
    # ex: /polls/5/vote/
    url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),

]
