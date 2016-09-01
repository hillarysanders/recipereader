from django.conf.urls import url

from . import views

app_name = 'polls'
urlpatterns = [
    # match to ''
    # ex: /polls/
    url(r'^$', views.index, name='index', kwargs=dict(a=10, b=20, c=30)),
    # ex: /polls/5/
    # note how the question_id argument is named. The value will be passed to views.detail(), which has
    # the named argument question_id. Pretty cool.
    url(r'^(?P<question_id>[0-9]+)/$', views.detail, name='detail'),
    # ex: /polls/5/results/
    url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    # ex: /polls/5/vote/
    url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
]
