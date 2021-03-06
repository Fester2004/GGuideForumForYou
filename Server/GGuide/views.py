from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash, get_user_model
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django import forms
from django.views.generic.edit import ModelFormMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.views.generic import CreateView
from django.views.generic.edit import ModelFormMixin
from django.forms.widgets import HiddenInput
from django.shortcuts import get_object_or_404
from GGuide.firebase import create_connect_firebase, log_in_connect_firebase, load_to_server_profile_images, \
    upload_files_profilemodel, upload_to_server_article_image, load_to_server_all_articles_images
from GGuide.models import ProfileModel, Comments, Article
from GGuide.forms import SignUpForm, Userlogin, ProfileForm, FriendForm, CommentsForm, ArticleForm


def sidebar_ctx():
    return {
        'users_images': load_to_server_profile_images(get_user_model().objects.all()),
        'articles_images': load_to_server_all_articles_images(Article.objects.all()),
        'articles': Article.objects.all(),
        'top_comments': Comments.objects.all().annotate(like_count=Count("likes")).order_by("-like_count")[:5],
    }


def index(request):
    ctx = {
        'articles': Article.objects.all()
    }
    ctx.update(sidebar_ctx())
    return render(request, 'index.html', context=ctx)


def articles(request):
    ctx = {
        'articles': Article.objects.all(),
    }
    ctx.update(sidebar_ctx())
    return render(request, 'articles/articles.html', context=ctx)


def article_create(request):
    ctx = {
        'articles': Article.objects.all(),
    }
    ctx.update(sidebar_ctx())

    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.cleaned_data.get("article_image")
            title = form.cleaned_data.get("header")
            text = form.cleaned_data.get("text")
            article_model = Article(article_image=img, text=text, title=title, author=request.user)
            article_model.save()
            upload_to_server_article_image(img, request.user)
            return redirect(article_model.get_absolute_url())
    else:
        form = ArticleForm()
    ctx['form'] = form
    return render(request, 'articles/create_article.html', ctx)


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    success_url = "/"
    ctx = {
        'article': article,
        'comments': article.comments.all(),
    }
    articles_images = load_to_server_all_articles_images(Article.objects.all())
    ctx.update(sidebar_ctx())
    user = request.user
    if request.method == 'POST':
        form = CommentsForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data.get('comment')
            comment_model = Comments(user=user, article=article, text=text)
            comment_model.save()

    return render(request, 'single-blog.html', ctx)


def game_views(request):
    ctx = sidebar_ctx()
    return render(request, 'game_index.html', ctx)


def blog_views(request):
    ctx = sidebar_ctx()

    return render(request, 'blog.html', context=ctx)


def cube_slam(request):
    return render(request, 'cube_slam.html', {})


def hexgl(request):
    return render(request, 'hexgl.html', {})


def gridgarden(request):
    return render(request, 'gridgarden.html', {})


def registration(request):
    success_url = "/"
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get("email")
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password, email=email)
            login(request, user)
            create_connect_firebase(user)
            p = ProfileModel(img='default.jpg', user=user)
            p.save()

            return redirect(success_url)
    else:
        form = SignUpForm()
    ctx = {
        'articles': Article.objects.all(),
        'form': form,
    }
    ctx.update(sidebar_ctx())
    return render(request, 'registration.html',ctx)


def logout(request, next_page='index'):

    return redirect(next_page)


def log_in(request):
    ctx = {
        'articles': Article.objects.all(),
    }
    ctx.update(sidebar_ctx())
    success_url = "/"
    if request.method == 'POST':
        form = Userlogin(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                log_in_connect_firebase(user)
                login(request, user)
                return redirect(success_url)
            else:
                return HttpResponse("Your account was inactive.")
    else:
        form = Userlogin()
    return render(request, 'log_in.html', ctx)


def profile_user(request):
    articles_count = Article.objects.all().filter(author=request.user).count()
    user_rank = 'noob'
    if articles_count >= 20:
        user_rank = 'advanced'
    if articles_count >= 50:
        user_rank = 'dominator'
    ctx = {
        'articles': Article.objects.all(),
        'articles_count': articles_count,
        'user_rank': user_rank,
    }
    ctx.update(sidebar_ctx())
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user  # user
            img = form.cleaned_data.get("Image") # user foto
            user.profile.img = img
            user.profile.save()
            upload_files_profilemodel(user, img)
    else:
        form = ProfileForm()
    ctx['form'] = form
    return render(request, 'profile.html', ctx)


def change_info(request):
    ctx = {
        'articles': Article.objects.all(),
    }
    ctx.update(sidebar_ctx())
    success_url = "/"
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect(success_url)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    ctx['form'] = form
    return render(request, 'change_password.html', ctx)


def friend_list(request):
    ctx = {
        'articles': Article.objects.all(),
    }
    ctx.update(sidebar_ctx())
    return render(request, 'friend_list.html', ctx)


def add_friend(request):
    ctx = {
        'articles': Article.objects.all(),
    }
    ctx.update(sidebar_ctx())
    if request.method == 'POST':
        form = FriendForm(request.POST)
        if form.is_valid():
            user = request.user
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            new_friend = User.objects.get(username=username, email=email)
            user.profile.friends.add(new_friend)
            user.profile.save()
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'add_friend.html', ctx)


def remove_friend(request):
    ctx = {
        'articles': Article.objects.all(),
    }
    ctx.update(sidebar_ctx())
    if request.method == 'POST':
        form = FriendForm(request.POST)
        if form.is_valid():
            user = request.user
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            friend = User.objects.get(username=username, email=email)
            user.profile.friends.remove(friend)
            user.profile.save()
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'remove_friend.html', ctx)


def article_likes(request, slug):
        article = get_object_or_404(Article, slug=slug)
        url = article.get_absolute_url()
        user = request.user
        if user.is_authenticated:
            if user in article.likes.all():
                article.likes.remove(user)
            else:
                article.likes.add(user)
        else:
            return redirect('login')

        return redirect(url)


def profile_user_articles(request):
    ctx = {
        'articles': Article.objects.all(),
        'user_articles': Article.objects.all().filter(author=request.user),
    }
    ctx.update(sidebar_ctx())

    return render(request, 'profile_articles.html', ctx)


def article_remove(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if article.author != request.user:
        return HttpResponse("You are not author", status_code=403)

    article.delete()
    return redirect('/your_articles/')


def comment_likes(request, id):
    comment = get_object_or_404(Comments, id=id)
    url = comment.article.get_absolute_url()
    user = request.user
    if user.is_authenticated:
        if user in comment.likes.all():
            comment.likes.remove(user)
        else:
            comment.likes.add(user)
    else:
        return redirect('login')

    return redirect(url)


def comment_remove(request, id):
    comment = get_object_or_404(Comments, id=id)
    if comment.user != request.user:
        return HttpResponse("You are not author", status_code=403)

    comment.delete()
    return redirect(comment.article.get_absolute_url())


