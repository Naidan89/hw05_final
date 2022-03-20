from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


AMT_SHOW_POSTS = 10


def index(request):
    posts = Post.objects.select_related('group')
    template = 'posts/index.html'
    paginator = Paginator(posts, AMT_SHOW_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    template = 'posts/group_list.html'
    paginator = Paginator(posts, AMT_SHOW_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists()
    )
    template = 'posts/profile.html'
    paginator = Paginator(posts, AMT_SHOW_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = Post.objects.get(pk=post_id)
    comments = Comment.objects.filter(post_id=post_id)
    form = CommentForm(request.POST or None)
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        temp_post = form.save(commit=False)
        temp_post.author = request.user
        temp_post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    is_edit = True
    if request.user != post.author:
        return redirect(post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': is_edit
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    authors = (Follow.objects.filter(user=request.user)
               .values_list('author_id', flat=True))
    posts = Post.objects.filter(author_id__in=authors)
    paginator = Paginator(posts, AMT_SHOW_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.username == username:
        return redirect('posts:profile', username=username)
    foll_author = get_object_or_404(User, username=username)
    check_follow = Follow.objects.filter(
        user=request.user,
        author=foll_author
    ).exists()
    if not check_follow:
        Follow.objects.create(user=request.user, author=foll_author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    foll_author = get_object_or_404(User, username=username)
    follower = get_object_or_404(Follow, author=foll_author, user=request.user)
    follower.delete()
    return redirect('posts:profile', username=username)
