from django.shortcuts import render, render_to_response
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.template import RequestContext
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views import generic
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Recipe
from .forms import UserForm, LoginForm, AddRecipeForm


# Create your views here.


def index(request):
    user = request.user  # can this be anonymous?
    context = {
        'user': user
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
                # save the new user profile:
                user.save()
                # go ahead and login the user:
                login(request, user)
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
            'createuserform': createuserform,
            'loginform': loginform
        }
        return render(request, 'home/login.html', context)


def add_recipe(request):

    if request.method == "POST":
        # add_recipe_form = AddRecipeForm(request.POST)
        add_recipe_form = AddRecipeForm(request.POST, request.FILES)  # TODO (image)
        if add_recipe_form.is_valid():
            recipe = add_recipe_form.save(commit=False)  # doesn't save the instance yet, since we need to add stuff
            recipe.user = request.user
            recipe.pub_date = timezone.now()
            recipe.save()
            return HttpResponseRedirect('/recipes/detail/{}/'.format(recipe.id))
        else:
            # no return redirect statement here, as errors will be shown in template below
            pass
    else:
        add_recipe_form = AddRecipeForm()

    context = {
        'add_recipe_form': add_recipe_form,
    }

    return render(request, 'home/add_recipe.html', context)


class RecipeDetailView(generic.DetailView):
    # note that this uses a generic.DetailView
    model = Recipe
    template_name = 'home/recipe_detail.html'


def cookbook(request):
    user = request.user
    user_recipes = Recipe.objects.filter(user=user.id)
    context = {
        'user': user,
        'recipes': user_recipes
    }
    return render(request, 'home/cookbook.html', context)


