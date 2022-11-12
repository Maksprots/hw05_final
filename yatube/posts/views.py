from django.shortcuts import render, \
    get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from .utils import make_paginator
from django.views.decorators.cache import cache_page


@cache_page(20)
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    context = {
        'page_obj': make_paginator(request, posts),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'page_obj': make_paginator(request, posts),
        'group': group,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = User.objects.get(username=username)
    posts = author.posts.all()
    following = (request.user.is_authenticated
                 and author.following.filter(user=request.user)
                 .exists()
                 )
    context = {
        'page_obj': make_paginator(request, posts),
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    author = User.objects.get(posts=post_id)
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'author': author,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST)
    template = 'posts/create_post.html'
    context = {
        'form': form,
    }
    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author.username)
        return render(request, template, context)
    else:
        return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user.id != post.author.id:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': make_paginator(request, posts),
    }
    template = 'posts/follow.html'
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        following = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(user=request.user,
                                     author=following)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following = User.objects.get(username=username)
    follower = get_object_or_404(Follow,
                                 author=following,
                                 user=request.user)
    follower.delete()
    return redirect('posts:profile', username=username)
