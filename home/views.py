from __future__ import unicode_literals
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
from . import conversions

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
        add_recipe_form = AddRecipeForm(request.POST, request.FILES)
        if add_recipe_form.is_valid():
            recipe = add_recipe_form.save(commit=False)  # doesn't save the instance yet, since we need to add stuff
            recipe.user = request.user

            recipe.ingredients = conversions.parse_ingredients(recipe.ingredients_text)
            # todo parse and save ingredients and directions here
            recipe.save()

            return HttpResponseRedirect('/recipes/detail/{}/'.format(recipe.id))
        else:
            # no return redirect statement here, as errors will be shown in template below
            pass
    else:
        add_recipe_form = AddRecipeForm()
        add_recipe_form.prep_time = 100

    context = {
        'add_recipe_form': add_recipe_form,
    }

    return render(request, 'home/add_recipe.html', context)


def get_highlighted_ingredients(recipe, prefix='<highlighted class="highlighted">', postfix='</highlighted>'):
    ing = recipe.ingredients
    idx = sorted(ing.keys())
    highlighted = []
    for i in idx:
        line = ing[i]['parsed_line']
        x = conversions.parse_ingredient_line(line)
        matches = x['matches']

        positions = sorted([[m['start'], m['end']] for m in matches.values()])
        h = ''
        end_ = 0
        for se in positions:
            start = se[0]
            end = se[1]
            h += line[end_:start]+prefix
            h += line[start:end]+postfix
            end_ = end
        h += line[end:len(line)]
        highlighted.append(h)

        # todo!! highlights ARE working (yay!) but the placement is off because the match positions refer to the line
        # todo   with e.g. '_(_' instead of '(' values, etc. I think ideally we want the output dict to contain
        # todo   start and end values of the final line, not the 'orginal' (actually, the preformatted) original line.

    return highlighted


class RecipeDetailView(generic.DetailView):
    # note that this uses a generic.DetailView
    model = Recipe
    template_name = 'home/recipe_detail.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(RecipeDetailView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['foo'] = get_highlighted_ingredients(context['recipe'])
        # context['foo'] = 'bar' # todo
        return context


def cookbook(request):
    user = request.user
    user_recipes = Recipe.objects.filter(user=user.id)
    context = {
        'user': user,
        'recipes': user_recipes
    }
    return render(request, 'home/cookbook.html', context)


