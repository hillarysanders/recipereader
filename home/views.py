from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.


def index(request):

    context = {
        'a': 1
    }
    # template = loader.get_template('polls/index.html')
    # return HttpResponse(template.render(context, request))
    return render(request, 'home/index.html', context)

