from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from .models import Comment, Post, Group, Follow
from .forms import PostForm, CommentForm

User = get_user_model()
CACHE_TIME = 20


def index(request):
    '''Главная страница'''
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page}
    )


def group_posts(request, slug):
    '''Страница группы'''
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page})


@login_required
def new_post(request):
    '''Создание нового поста'''
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new_post.html', {'form': form,
                  'is_edit': False})


def profile(request, username):
    '''Страница профиля пользователя'''
    author = User.objects.get(username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists()
    )
    context = {
        'author': author,
        'username': username,
        'page': page,
        'following': following
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    '''Страница поста'''
    requested_post = Post.objects.get(pk=post_id)
    comments = Comment.objects.filter(post=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'author': requested_post.author,
        'username': username,
        'requested_post': requested_post,
        'form': form,
        'comments': comments
    }
    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    '''Страница редактирования поста'''
    if request.user.username != username:
        return redirect('post', username, post_id)
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'new_post.html',
                  {'form': form, 'is_edit': True,
                   'post': post})


@login_required
def add_comment(request, username, post_id):
    '''Добавление комментария на странице поста'''
    form = CommentForm(request.POST or None)
    requested_post = get_object_or_404(Post, id=post_id,
                                       author__username=username)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = requested_post
        comment.save()
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    '''Страница подписок'''
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page})


@login_required
def profile_follow(request, username):
    '''Подписка на пользователя (кнока на странице профиля пользователя)'''
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    '''Отписка от пользователя (кнока на странице профиля пользователя)'''
    follow_link = get_object_or_404(Follow, user=request.user,
                                    author__username=username)
    follow_link.delete()
    return redirect('profile', username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
