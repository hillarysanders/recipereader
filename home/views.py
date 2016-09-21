from __future__ import unicode_literals
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.views import generic
from django.shortcuts import render, get_object_or_404
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib import messages
import logging
from .models import Recipe, UserProxy
from .forms import UserForm, LoginForm, AddRecipeForm
from . import conversions

# Create your views here.


def index(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'home/index.html', context)


def welcome(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'home/welcome.html', context)


def profile(request):
    # todo add to this view. first need to sup up userProxy model.
    
    user = request.user  # can this be anonymous?
    print(user)
    user_proxy = get_user_proxy(request)
    recipes = Recipe.objects.filter(user_proxy=user_proxy)
    for r in recipes:
        print(r)
    print(len(recipes))
    context = {
        'user': user,
        'n_recipes': '1 recipe' if len(recipes) == 1 else '{} recipes'.format(len(recipes)),
        'most_recent_recipe': str(max([r.pub_date for r in recipes]))[:10]
    }
    return render(request, 'home/profile.html', context)


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')


def auth_login(request):
    error_messages = ''
    if request.method == "POST":
        # if the user clicked the create user submit button:
        if request.POST.get("createUserSubmit"):
            uform = UserForm(data=request.POST)
            print(uform)
            if uform.is_valid():
                user = uform.save()
                # save the new user profile:
                user.save()

                # for now, automatically import session recipes:
                if request.session.session_key is not None:
                    user_proxy, created = UserProxy.objects.get_or_create(session=request.session.session_key)
                    print(user_proxy)
                    user_proxy.user = user
                    user_proxy.session = ''
                    user_proxy.save()

                # go ahead and login the user:
                login(request, user)
                return HttpResponseRedirect('/welcome/')
            else:
                error_messages = uform.errors
        # if the user clicked the login submit button:
        elif request.POST.get("loginSubmit"):
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page.
                return HttpResponseRedirect('/welcome/')
            else:
                # todo make this into an actual error
                error_messages = {'message': 'Invalid username / password. Try again?'}


    createuserform = UserForm()
    loginform = LoginForm()

    context = {
        'createuserform': createuserform,
        'loginform': loginform,
        'error_messages': error_messages
    }
    return render(request, 'home/login.html', context)


# def get_or_none(model, *args, **kwargs):
#     try:
#         return model.objects.get(*args, **kwargs)
#     except model.DoesNotExist:
#         return None


def get_user_proxy(request):
    # if the session key is None, then they don't have a cookie yet (?), so give em' one.
    if request.session.session_key is None:
        request.session.save()

    logged_in_user = request.user
    if logged_in_user.id is None:
        #  no user is logged in:
        obj, created = UserProxy.objects.get_or_create(session=request.session.session_key, user=None)
    else:
        obj, created = UserProxy.objects.get_or_create(user=logged_in_user, session='')

    user_proxy = obj

    # now you need to save the session instance so it can be accessed later
    # request.session.modified = True

    return user_proxy


def cookbook(request):
    user_proxy = get_user_proxy(request)
    print('cookbook view: user proxy:')
    print(user_proxy)
    recipes = Recipe.objects.filter(user_proxy=user_proxy).order_by('recipe_name')

    if request.method == 'GET':
        search_text = request.GET.get('search', None)
        if search_text:
            if search_text != '':
                vector = SearchVector('recipe_name', 'ingredients_text', 'description')
                query = SearchQuery(search_text)
                recipes = recipes.annotate(rank=SearchRank(vector, query)).order_by('-rank').filter(rank__gt=0)

    context = {
        'recipes': recipes
    }
    return render(request, 'home/cookbook.html', context)


def add_recipe(request):

    if request.method == "POST":
        add_recipe_form = AddRecipeForm(request.POST, request.FILES)
        if add_recipe_form.is_valid():
            recipe = add_recipe_form.save(commit=False)  # doesn't save the instance yet, since we need to add stuff
            # recipe.user = request.user
            recipe.user_proxy = get_user_proxy(request)
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

    print('\tSESSION KEY in ADD_RECIPE VIEW: ')
    print(request.session.session_key)

    return render(request, 'home/add_recipe.html', context)


def edit_recipe(request, pk):

    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        # instance = recipe tells this that it's an update
        add_recipe_form = AddRecipeForm(request.POST, request.FILES, instance=recipe)
        if add_recipe_form.is_valid():
            recipe = add_recipe_form.save(commit=False)  # doesn't save the instance yet, since we need to add stuff
            # recipe.user = request.user
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


def about(request):
    context = dict()
    return render(request, 'home/about.html')