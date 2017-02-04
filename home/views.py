from __future__ import unicode_literals
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, get_object_or_404
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
import json
import itertools
from . import models
from .forms import UserForm, LoginForm, AddRecipeForm
from .conversions_utils import highlight_changed_amounts
from . import conversions
# Create your views here.
from django.views.decorators.csrf import csrf_exempt
# todo hack ^^

stash_tooltips = {'-': 'Remove recipe from personal stash?',
                  '+': 'Add recipe to personal stash?'}


def index(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'home/index.html', context)


def cookbook(request):
    user_proxy = get_user_proxy(request)

    if request.GET.get('public_search', False):
        recipes = models.Recipe.objects.filter(Q(public=True) | Q(user_proxy=user_proxy)).order_by('recipe_name')
    else:
        stashed = user_proxy.stashed_recipes.all()
        recipes = models.Recipe.objects.filter(Q(id__in=[r.id for r in stashed]) | Q(user_proxy=user_proxy))

    search_text = ''
    if request.method == 'GET':
        search_text = request.GET.get('search', '')
        if search_text != '':

            vector = SearchVector('recipe_name', weight='A') +\
                     SearchVector('ingredients_text', weight='B') +\
                     SearchVector('description', weights='C')
            query = SearchQuery(search_text)

            # tri_sim = 3*(TrigramSimilarity('recipe_name', search_text))+TrigramSimilarity('ingredients_sans_amounts',
            #                                                                               search_text)
            tri_sim = TrigramSimilarity('recipe_name', search_text)
            recipes = recipes.annotate(similarity=tri_sim).filter(similarity__gt=0.01)
            # now reorder by best full match, followed by best (fuzzy match) similarity:
            recipes = recipes.annotate(rank=SearchRank(vector, query)).order_by('-rank', '-similarity')
            # print(type(tri_sim))
            # print(tri_sim)
            # for r in recipes:
            #     print(r.recipe_name)
            #     print(r.similarity)
            #     print(r.rank)
            #     print('________________________________')

    context = {
        'recipes': recipes,
        'public_search_attr': 'checked="checked"' if request.GET.get('public_search', False) else '',
        'search_text': search_text
    }

    # all = models.Recipe.objects.order_by('recipe_name')
    # for r in all:
    #     r.save()

    return render(request, 'home/cookbook.html', context)


def welcome(request):
    return render(request, 'home/welcome.html', {})


def ajax_validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': models.User.objects.filter(username__iexact=username).exists()
    }
    if data['is_taken']:
        data['error_message'] = "A user with the username '{}' already exists.".format(username)

    return JsonResponse(data)


def public_profile(request, username):
    user = models.User.objects.get(username=username)
    if user:
        user_proxy = models.UserProxy.objects.get(user=user)
        recipes = models.Recipe.objects.filter(user_proxy=user_proxy)

        if len(recipes) > 0:
            most_recent_recipe = str(max([r.pub_date for r in recipes]))[:10]
            n_recipes = '1 recipe' if len(recipes) == 1 else '{} recipes'.format(len(recipes))
        else:
            most_recent_recipe = "Aw man, they haven't saved any yet"
            n_recipes = '0 recipes so far'

        context = {
            'this_user': user,
            'n_recipes': n_recipes,
            'most_recent_recipe': most_recent_recipe
        }
        return render(request, 'home/profile.html', context)
    else:
        return render(request, 'home/message.html', dict(message="hrm, sorry, I don't think that user exists."))


@login_required
def profile(request):

    user = request.user  # can this be anonymous?
    user_proxy = get_user_proxy(request)
    recipes = models.Recipe.objects.filter(user_proxy=user_proxy)

    if len(recipes) > 0:
        most_recent_recipe = str(max([r.pub_date for r in recipes]))[:10]
        n_recipes = '1 recipe' if len(recipes) == 1 else '{} recipes'.format(len(recipes))
    else:
        most_recent_recipe = "Aw man, you haven't saved any yet"
        n_recipes = '0 recipes so far'
    context = {
        'this_user': user,
        'n_recipes': n_recipes,
        'most_recent_recipe': most_recent_recipe
    }
    return render(request, 'home/profile.html', context)


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/login/')


@csrf_exempt
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
                    user_proxy, created = models.UserProxy.objects.get_or_create(session=request.session.session_key)
                    user_proxy.user = user
                    user_proxy.session = ''
                    user_proxy.save()

                # go ahead and login the user:
                login(request, user)
                return HttpResponseRedirect('/')
            else:
                error_messages = uform.errors
        # if the user clicked the login submit button:
        elif request.POST.get("loginSubmit"):
            username = request.POST['login_username']
            password = request.POST['login_password']

            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page.
                return HttpResponseRedirect('/')
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


def get_user_proxy(request):
    # if the session key is None, then they don't have a cookie yet (?), so give em' one.
    if request.session.session_key is None:
        request.session.save()

    logged_in_user = request.user
    if logged_in_user.id is None:
        #  no user is logged in:
        obj, created = models.UserProxy.objects.get_or_create(session=request.session.session_key, user=None)
    else:
        obj, created = models.UserProxy.objects.get_or_create(user=logged_in_user, session='')

    user_proxy = obj

    # now you need to save the session instance so it can be accessed later
    # request.session.modified = True

    return user_proxy


def check_if_owned_by_user(request, recipe):
    user_proxy = get_user_proxy(request)
    recipes_user = recipe.user_proxy
    has_perm = user_proxy == recipes_user
    return has_perm


@csrf_exempt
def add_recipe(request):

    context = dict(add_recipe_form=AddRecipeForm(),
                   update='',
                   title='Add a Recipe')

    if request.method == "POST":
        add_recipe_form = AddRecipeForm(request.POST, request.FILES)
        if add_recipe_form.is_valid():
            # posted? todo (image)
            context['posted'] = add_recipe_form.instance
            recipe = add_recipe_form.save(commit=False)  # doesn't save the instance yet, since we need to add stuff
            recipe.user_proxy = get_user_proxy(request)
            recipe.save()

            return HttpResponseRedirect(reverse('home:recipe_detail', args=(recipe.slug, recipe.pk)))
        else:
            # no return redirect statement here, as errors will be shown in template below
            pass

    return render(request, 'home/add_recipe.html', context)

@csrf_exempt
def edit_recipe(request, slug, pk):

    recipe = get_object_or_404(models.Recipe, pk=pk)
    if request.method == "POST":
        if check_if_owned_by_user(request, recipe):
            # instance = recipe tells this that it's an update
            add_recipe_form = AddRecipeForm(request.POST, request.FILES, instance=recipe)
            if add_recipe_form.is_valid():
                recipe = add_recipe_form.save(commit=False)  # doesn't save the instance yet, since we need to add stuff
                # recipe.user = request.user
                recipe.save()

                return HttpResponseRedirect(reverse('home:recipe_detail', args=(slug, pk)))
            else:
                # no return redirect statement here, as errors will be shown in template below
                pass
        else:
            return HttpResponseRedirect(reverse('home:bad_perm'))
    else:
        add_recipe_form = AddRecipeForm(instance=recipe)

    context = {
        'add_recipe_form': add_recipe_form,
        'update': 'Update',
        'title': 'Edit Recipe'
    }

    return render(request, 'home/add_recipe.html', context)


def bad_perm(request):
    context = {
        'message': "Ruh roh! Looks like you didn't have permission to do that."
    }
    return render(request, 'home/message.html', context)


@csrf_exempt
def ajax_change_servings(request):

    ingredients = json.loads(request.POST.get('ingredients', None))
    instructions = json.loads(request.POST.get('instructions', None))
    most_recent_servings = request.POST.get('most_recent_servings', None)
    servings = request.POST.get('servings', None)

    ingredients = conversions.change_servings(ingredients=ingredients,
                                              convert_sisterless_numbers=True,
                                              servings0=most_recent_servings,
                                              servings1=servings)

    instructions = conversions.change_servings(ingredients=instructions,
                                               convert_sisterless_numbers=True,
                                               servings0=most_recent_servings,
                                               servings1=servings)

    data = dict(
        servings=servings,
        ingredients=json.dumps(ingredients, cls=DjangoJSONEncoder),
        instructions=json.dumps(instructions, cls=DjangoJSONEncoder),
        hi_ingredients=highlight_changed_amounts(ingredients,
                                                 convert_sisterless_numbers=True,
                                                 ingredients=True),
        hi_instructions=highlight_changed_amounts(instructions,
                                                  convert_sisterless_numbers=True,
                                                  ingredients=False)
    )

    return JsonResponse(data)

@csrf_exempt
def ajax_change_units(request):
    # todo now we just need to create the conversions.change_units() function,
    # todo and then after than, make it so servings conversion is done via ajax as well! :)
    ingredients = json.loads(request.POST.get('ingredients', None))
    instructions = json.loads(request.POST.get('instructions', None))
    units_type = request.POST.get('units_type', None)

    ingredients = conversions.change_units(ingredients, units_type=units_type)
    instructions = conversions.change_units(instructions, units_type=units_type)
    # ingredients['0']['match_info']['0.0']['name'] = '{} {}'.format('Changed units to {}'.format(units_type),
    #                                                                ingredients['0']['match_info']['0.0']['name'])

    data = dict(
        units_type=units_type,
        ingredients=json.dumps(ingredients, cls=DjangoJSONEncoder),
        instructions=json.dumps(instructions, cls=DjangoJSONEncoder),
        hi_ingredients=highlight_changed_amounts(ingredients,
                                                 convert_sisterless_numbers=True,
                                                 ingredients=True),
        hi_instructions=highlight_changed_amounts(instructions,
                                                  convert_sisterless_numbers=True,
                                                  ingredients=False)
    )
    return JsonResponse(data)


def delete_recipe(request, pk):
    recipe = get_object_or_404(models.Recipe, pk=pk)

    if recipe:
        if check_if_owned_by_user(request, recipe):
            message = 'Your recipe ({}) was successfully deleted.'.format(recipe.recipe_name)
            recipe.delete()
            messages.success(request, "Your recipe was successfully deleted.")
        else:
            message = "Ruh roh! Looks like you don't have permission to delete that, only the lovely '{}' does".format(
                recipe.user_proxy)

    else:
        message = 'Hmmmm. Recipe not found. :('

    context = {
        'message': message
    }

    return render(request, 'home/message.html', context)


def about(request):
    context = dict()
    return render(request, 'home/about.html')


def recipe_detail(request, slug, pk):
    recipe = get_object_or_404(models.Recipe, pk=pk)

    context = {
        'recipe': recipe,
        'initial_servings': recipe.num_servings
    }

    ingredients = recipe.ingredients
    instructions = recipe.instructions

    context['ingredients'] = json.dumps(ingredients, cls=DjangoJSONEncoder)
    context['instructions'] = json.dumps(instructions, cls=DjangoJSONEncoder)
    context['hi_ingredients'] = highlight_changed_amounts(ingredients, convert_sisterless_numbers=True,
                                                          ingredients=True)
    context['hi_instructions'] = highlight_changed_amounts(instructions, convert_sisterless_numbers=True)

    user_proxy = get_user_proxy(request)
    if user_proxy.stashed_recipes.filter(pk=recipe.pk).exists():
        stash_plus_or_minus = '-'
    else:
        stash_plus_or_minus = '+'
    context['stash_plus_or_minus'] = stash_plus_or_minus
    context['stash_tooltip'] = stash_tooltips.get(stash_plus_or_minus)

    if recipe.bw_pngs is not None:
        context['bw_pngs'] = [png for png in recipe.bw_pngs]
        print(context['bw_pngs'])

    return render(request, 'home/recipe_view.html', context)


def ajax_add_recipe_to_stash(request):

    recipe_pk = request.GET.get('recipe_pk', None)
    stash_plus_or_minus = request.GET.get('stash_plus_or_minus', None)
    user_proxy = get_user_proxy(request)
    recipe = models.Recipe.objects.get(pk=recipe_pk)

    if stash_plus_or_minus == '+':
        user_proxy.stashed_recipes.add(recipe)
        stash_plus_or_minus = '-'
    else:
        user_proxy.stashed_recipes.remove(recipe)
        stash_plus_or_minus = '+'

    stash_tooltip = stash_tooltips.get(stash_plus_or_minus)

    data = dict(stash_plus_or_minus=stash_plus_or_minus,
                stash_tooltip=stash_tooltip)

    return JsonResponse(data)


# def csrf_failure(request, reason=''):
#     ctx = {'message': 'some custom messages'}
#     return render(request, 'home/csrf_failure.html', ctx)












