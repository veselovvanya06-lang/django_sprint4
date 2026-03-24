from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, UpdateView

from .models import Category, Post, Comment
from .forms import PostForm, UserForm, CommentForm

POSTS_PER_PAGE = 10

def index(request):
    posts = Post.objects.select_related('category', 'location', 'author').annotate(
        comment_count=Count('comments')).filter(
        pub_date__lte=timezone.now(), is_published=True, category__is_published=True
    )
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/index.html', {'page_obj': page_obj})

def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not post.is_published and post.author != request.user:
        return redirect('blog:index')
    comments = post.comments.all()
    form = CommentForm()
    return render(request, 'blog/detail.html', {'post': post, 'form': form, 'comments': comments})

def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, is_published=True)
    posts = Post.objects.filter(category=category, is_published=True, pub_date__lte=timezone.now())
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/category.html', {'category': category, 'page_obj': page_obj})

def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author).annotate(comment_count=Count('comments'))
    if request.user != author:
        posts = posts.filter(is_published=True, pub_date__lte=timezone.now())
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/profile.html', {'profile': author, 'page_obj': page_obj})

class RegistrationView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('blog:index')

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    def test_func(self):
        return self.get_object().author == self.request.user
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    def test_func(self):
        return self.get_object().author == self.request.user
    def get_success_url(self):
        return reverse_lazy('blog:index')

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'
    def get_object(self): return self.request.user
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})

def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)

class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    def test_func(self): return self.get_object().author == self.request.user
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})

class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    def test_func(self): return self.get_object().author == self.request.user
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})