from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.http import Http404
from django.urls import reverse
from django.views import generic
from .models import Question, Choice
# Create your views here.


def index(request, **kwargs):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    context = {
        'latest_question_list': latest_question_list,
        'kwargs': kwargs
    }
    # template = loader.get_template('polls/index.html')
    # return HttpResponse(template.render(context, request))
    return render(request, 'polls/index.html', context)


class DetailView(generic.DetailView):
    # note that this uses a generic.DetailView
    model = Question
    template_name = 'polls/detail.html'


class ResultsView(generic.DetailView):
    # note that this uses a generic.DetailView
    model = Question
    template_name = 'polls/results.html'


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        # request.POST is a dictionary like object that lets you access submitted data by key name
        # In this case, request.POST['choice'] returns the id of the selected choice, always as a string.
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
        # ^^ this reverse() function will return a string like: '/polls/3/results/'.
        # reverse() is given the name of the view that we want to pass control to and the variable portion of the
        # URL pattern that points to that view, based on polls/urls.py.results.

