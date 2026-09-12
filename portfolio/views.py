from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContactForm
from .models import Experience, GalleryImage, Post, Profile, Project, Skill


# ---------------------------------------------------------------------------
# Home — featured posts + category tabs
# ---------------------------------------------------------------------------
def home(request):
    featured_posts = Post.objects.filter(status=True, featured=True)[:3]
    featured_projects = Project.objects.filter(featured=True)[:2]

    categories = []
    for value, label in Post.Category.choices:
        posts = Post.objects.filter(status=True, category=value)[:3]
        if posts:
            categories.append({'value': value, 'label': label, 'posts': posts})

    latest_posts = Post.objects.filter(status=True)[:6]

    context = {
        'featured_posts': featured_posts,
        'featured_projects': featured_projects,
        'categories': categories,
        'latest_posts': latest_posts,
    }
    return render(request, 'portfolio/home.html', context)


# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------
def about(request):
    profile = Profile.objects.first()
    experiences = Experience.objects.filter(profile=profile).order_by('order', '-start_date') if profile else []
    skills = Skill.objects.filter(profile=profile).order_by('order', '-percent') if profile else []
    context = {
        'experiences': experiences,
        'skills': skills,
    }
    return render(request, 'portfolio/about.html', context)


# ---------------------------------------------------------------------------
# Work (projects)
# ---------------------------------------------------------------------------
def work_list(request):
    projects = Project.objects.all().prefetch_related('tags')

    tag_slug = request.GET.get('tag')
    if tag_slug:
        projects = projects.filter(tags__slug=tag_slug)

    paginator = Paginator(projects, settings.PROJECTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'projects': page_obj.object_list,
        'active_tag': tag_slug,
    }
    return render(request, 'portfolio/work_list.html', context)


def work_detail(request, slug):
    project = get_object_or_404(Project.objects.prefetch_related('images', 'tags'), slug=slug)
    related_projects = (
        Project.objects.filter(tags__in=project.tags.all())
        .exclude(pk=project.pk).distinct()[:3]
    )
    context = {
        'project': project,
        'related_projects': related_projects,
    }
    return render(request, 'portfolio/work_detail.html', context)


# ---------------------------------------------------------------------------
# Blog
# ---------------------------------------------------------------------------
def blog_list(request):
    posts = Post.objects.filter(status=True).prefetch_related('tags')

    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        posts = posts.filter(
            Q(title__icontains=keyword)
            | Q(excerpt__icontains=keyword)
            | Q(content__icontains=keyword)
        )

    category = request.GET.get('category')
    if category:
        posts = posts.filter(category=category)

    paginator = Paginator(posts, settings.BLOG_POSTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'posts': page_obj.object_list,
        'keyword': keyword,
        'active_category': category,
        'categories': Post.Category.choices,
    }
    return render(request, 'portfolio/blog_list.html', context)


def blog_detail(request, slug):
    post = get_object_or_404(Post.objects.prefetch_related('tags'), slug=slug, status=True)
    related_posts = (
        Post.objects.filter(status=True, category=post.category)
        .exclude(pk=post.pk)[:3]
    )
    context = {
        'post': post,
        'related_posts': related_posts,
    }
    return render(request, 'portfolio/blog_detail.html', context)


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------
def gallery(request):
    images = GalleryImage.objects.all()
    context = {'images': images}
    return render(request, 'portfolio/gallery.html', context)


# ---------------------------------------------------------------------------
# Contact — real POST handler that saves to the database
# ---------------------------------------------------------------------------
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thanks! Your message has been sent — I'll get back to you soon.",
            )
            return redirect('portfolio:contact')
        messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = ContactForm()

    context = {'form': form}
    return render(request, 'portfolio/contact.html', context)
