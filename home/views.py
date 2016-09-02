from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from .forms import UserForm, LoginForm


# Create your views here.


def index(request):

    context = {
        'a': 1
    }
    # template = loader.get_template('polls/index.html')
    # return HttpResponse(template.render(context, request))
    return render(request, 'home/index.html', context)


def auth_login(request):

    if request.method == "POST":
        # if the user clicked the create user submit button:
        if request.POST.get("createUserSubmit"):
            uform = UserForm(data=request.POST)
            if uform.is_valid():
                user = uform.save()
                user.save()
                return HttpResponseRedirect('/home/')
            else:
                return HttpResponse('Invalid Inputs. :( Try again? <3')
        # if the user clicked the login submit button:
        elif request.POST.get("loginSubmit"):
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page.
                return HttpResponseRedirect('/home/')
            else:
                # Return an 'invalid login' error message.
                return HttpResponse('Invalid username / password. :( Try again? <3')

    else:
        createuserform = UserForm()
        loginform = LoginForm()

        context = {
            'a': 1,
            'createuserform': createuserform,
            'loginform': loginform
        }
        # template = loader.get_template('polls/index.html')
        # return HttpResponse(template.render(context, request))
        return render(request, 'home/login.html', context)





