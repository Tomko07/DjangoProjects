from datetime import datetime

from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect

from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm


def index(request):

    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list, 'pages': page_list}

    visits = request.session.get('visits')
    if not visits:
        visits = 1
    reset_last_visit_time = False

    last_visit = request.session.get('last_visit')

    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")
        if (datetime.now() - last_visit_time).days > 0:
            visits += 1
            reset_last_visit_time = True

    else:
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    context_dict['visits'] = visits


    return render(request, 'rango/index.html', context_dict)


def about(request):

    context_dict = {'emphasizedmsg': "(unicorns as well!)"}

    visits = request.session.get('visits')
    if not visits:
        visits = 1

    context_dict['visits'] = visits

    return render(request, 'rango/about.html', context_dict)


def category(request, category_name_slug):

    context_dict = {}

    try:
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name

        pages = Page.objects.filter(category=category)

        context_dict['pages'] = pages
        context_dict['category'] = category
        context_dict['slug'] = category_name_slug

    except Category.DoesNotExist:
        pass

    return render(request, 'rango/category.html', context_dict)


@login_required
def add_category(request):

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            cat = form.save(commit=True)
            print cat, cat.slug
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()

    return render(request, 'rango/add_category.html', {'form': form})


@login_required
def add_page(request, category_name_slug):

    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        cat = None

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                # page.views = 0
                page.save()
                return category(request, category_name_slug)
        else:
            print form.errors
    else:
        form = PageForm()

    context_dict = {'form': form, 'category': cat, 'user': request.user}

    return render(request, 'rango/add_page.html', context_dict)


def register(request):

    registered = False

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()

            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            profile.save()

            registered = True

        else:
            print user_form.errors, profile_form.errors

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    context_dict = dict()
    context_dict['user_form'] = user_form
    context_dict['profile_form'] = profile_form
    context_dict['registered'] = registered

    return render(request, 'rango/register.html', context_dict)


def user_login(request):
    authenticated = False
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango')
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)

    return render(request, 'rango/login.html', {'authenticated': authenticated})


@login_required
def restricted(request):
    render(request, 'rango/restricted.html', {})


@login_required
def user_logout(request):
    logout(request)

    return HttpResponseRedirect('/rango/')
