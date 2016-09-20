from __future__ import unicode_literals
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.views import generic
from django.shortcuts import render, get_object_or_404
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib import messages
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

    message = error_messages = ''
    if request.method == "POST":
        # if the user clicked the create user submit button:
        if request.POST.get("createUserSubmit"):
            uform = UserForm(data=request.POST)
            print(uform)
            if uform.is_valid():
                user = uform.save()
                # save the new user profile:
                user.save()
                # go ahead and login the user:
                login(request, user)
                return HttpResponseRedirect('/home/')
            else:
                message = 'Invalid inputs. :( Try again? <3'
                error_messages = uform.errors
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
                message = 'Invalid username / password. :( Try again? <3'


    createuserform = UserForm()
    loginform = LoginForm()

    context = {
        'createuserform': createuserform,
        'loginform': loginform,
        'error_messages': error_messages,
        'message': message
    }
    return render(request, 'home/login.html', context)


def add_recipe(request):

    if request.method == "POST":
        add_recipe_form = AddRecipeForm(request.POST, request.FILES)
        if add_recipe_form.is_valid():
            recipe = add_recipe_form.save(commit=False)  # doesn't save the instance yet, since we need to add stuff
            recipe.user = request.user
            recipe.save()

            return HttpResponseRedirect('/recipes/detail/{}/'.format(recipe.id))
        else:
            # no return redirect statement here, as errors will be shown in template below
            pass
    else:
        add_recipe_form = AddRecipeForm()

    context = {
        'add_recipe_form': add_recipe_form,
        'update': '',
        'title': 'Add a Recipe'
    }

    return render(request, 'home/add_recipe.html', context)


def edit_recipe(request, pk):

    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        # instance = recipe tells this that it's an update
        add_recipe_form = AddRecipeForm(request.POST, request.FILES, instance=recipe)
        if add_recipe_form.is_valid():
            recipe = add_recipe_form.save(commit=False)  # doesn't save the instance yet, since we need to add stuff
            recipe.user = request.user
            recipe.save()

            return HttpResponseRedirect('/recipes/detail/{}/'.format(recipe.id))
        else:
            # no return redirect statement here, as errors will be shown in template below
            pass
    else:
        add_recipe_form = AddRecipeForm(instance=recipe)

    context = {
        'add_recipe_form': add_recipe_form,
        'update': 'Update',
        'title': 'Edit Recipe'
    }

    return render(request, 'home/add_recipe.html', context)


class RecipeDetailView(generic.DetailView):
    # note that this uses a generic.DetailView
    model = Recipe
    template_name = 'home/recipe_detail.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(RecipeDetailView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['highlighted_ingredients'] = conversions.get_highlighted_ingredients(context['recipe'].ingredients)
        context['highlighted_instructions'] = conversions.get_highlighted_ingredients(context['recipe'].instructions)
        return context


def delete_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if recipe:
        context = {
            'message': 'Your recipe ({}) was successfully deleted.'.format(recipe.recipe_name)
        }
        recipe.delete()
        messages.success(request, "Your recipe was successfully deleted.")

        return render(request, 'home/message.html', context)


def cookbook(request):
    user = request.user
    recipes = Recipe.objects.filter(user=user.id).order_by('recipe_name')

    if request.method == 'GET':
        search_text = request.GET.get('search', None)
        if search_text:
            if search_text != '':
                vector = SearchVector('recipe_name', 'ingredients_text', 'description')
                query = SearchQuery(search_text)
                recipes = recipes.annotate(rank=SearchRank(vector, query)).order_by('-rank').filter(rank__gt=0)

    context = {
        'user': user,
        'recipes': recipes
    }
    return render(request, 'home/cookbook.html', context)


def about(request):
    context = dict()
    return render(request, 'home/about.html')