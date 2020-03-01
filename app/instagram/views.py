from datetime import timedelta
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import PostForm, CommentForm
from .models import Tag, Post


@login_required
def index(request):
    time_since = timezone.now() - timedelta(days=3)
    # post_list = Post.objects.all().filter(Q(author=request.user) | Q(author__in=request.user.following_set.all()))
    post_list = Post.objects.all().filter(Q(author__in=request.user.following_set.all())) \
        .filter(created_at__gte=time_since)
    suggested_user_list = get_user_model().objects.all() \
                              .exclude(pk=request.user.pk) \
                              .exclude(pk__in=request.user.following_set.all())[:3]
    comment_form = CommentForm()
    return render(request, 'instagram/index.html', {
        'post_list': post_list,
        'suggested_user_list': suggested_user_list,
        'comment_form': comment_form,
    })


@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            post.tag_set.add(*post.extract_tag_list())  # list 로 add 하니까 개별로 들어가내...
            messages.success(request, '포스팅 저장')
            return redirect(post)  # get_absolute_url
    else:
        form = PostForm()
    return render(request, 'instagram/post_new_form.html', {
        'form': form,
    })


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comment_form = CommentForm()
    return render(request, 'instagram/post_detail.html', {
        'post': post,
        'comment_form': comment_form,
    })


def user_page(request, username):
    page_user = get_object_or_404(get_user_model(), username=username, is_active=True)

    if request.user.is_authenticated:
        is_follow = request.user.following_set.filter(pk=page_user.pk).exists()
    else:
        is_follow = False

    post_list = Post.objects.filter(author=page_user)
    post_list_count = post_list.count()
    return render(request, 'instagram/user_page.html', {
        'page_user': page_user,
        'post_list': post_list,
        'post_list_count': post_list_count,
        'is_follow': is_follow,
    })


@login_required
def post_like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.like_user_set.add(request.user)
    messages.success(request, f'{post}를 좋아합니다.')
    redirect_url = request.META.get('HTTP_REFERER', 'instagram:index')
    return redirect(redirect_url)


@login_required
def post_unlike(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.like_user_set.remove(request.user)
    messages.success(request, f'{post}를 좋아요를 취소합니다.')
    redirect_url = request.META.get('HTTP_REFERER', 'instagram:index')
    return redirect(redirect_url)


@login_required
def comment_new(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk)

    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            if request.is_ajax():
                return render(request, 'instagram/_comment.html', {
                    'comment': comment,
                })
            redirect_url = request.META.get('HTTP_REFERER', comment.post)
            return redirect(redirect_url)
    else:
        form = CommentForm()
    return render(request, 'instagram/comment_form.html', {
        'form': form,
    })