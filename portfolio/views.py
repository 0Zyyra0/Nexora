from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    ContactForm,
    ProfileEditForm,
    RecoverAnswerForm,
    RecoverIdentifyForm,
    RegisterForm,
    SecurityQuestionEditForm,
)
from .site_texts import get_text
from .models import (
    Bookmark,
    Comment,
    Experience,
    GalleryImage,
    Like,
    Post,
    Profile,
    Project,
    SecurityCredential,
    Skill,
)

User = get_user_model()


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


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

    # Only approved, top-level comments are shown; each carries its
    # approved replies (fetched below) to render as a single thread level.
    top_comments = list(
        post.comments.filter(status=Comment.Status.APPROVED, parent__isnull=True)
        .select_related('user')
    )
    approved_replies = post.comments.filter(status=Comment.Status.APPROVED, parent__isnull=False)
    replies_by_parent = {}
    for reply in approved_replies:
        replies_by_parent.setdefault(reply.parent_id, []).append(reply)
    my_comment_ids = set(request.session.get('my_comment_ids', []))

    def _mark(comment):
        comment.can_delete = (
            comment.id in my_comment_ids
            or (request.user.is_authenticated and comment.user_id == request.user.id)
        )
        return comment

    for comment in top_comments:
        comment.visible_replies = [_mark(r) for r in replies_by_parent.get(comment.id, [])]
        _mark(comment)

    if request.user.is_authenticated:
        initial = {'name': request.user.get_full_name() or request.user.username, 'email': request.user.email}
    else:
        initial = None
    comment_form = CommentForm(initial=initial)

    session_key = request.session.session_key
    liked = bool(session_key) and post.likes.filter(session_key=session_key).exists()
    bookmarked = (
        request.user.is_authenticated
        and Bookmark.objects.filter(user=request.user, post=post).exists()
    )

    context = {
        'post': post,
        'related_posts': related_posts,
        'comments': top_comments,
        'comment_form': comment_form,
        'my_comment_ids': my_comment_ids,
        'like_count': post.likes.count(),
        'liked': liked,
        'bookmarked': bookmarked,
    }
    return render(request, 'portfolio/blog_detail.html', context)


@require_POST
def comment_create(request, slug):
    post = get_object_or_404(Post, slug=slug, status=True)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.ip_address = _client_ip(request)
        parent_id = request.POST.get('parent')
        if parent_id:
            comment.parent = get_object_or_404(Comment, pk=parent_id, post=post)
        if request.user.is_authenticated:
            comment.user = request.user

        comment.save()

        # Remember this comment belongs to this browser so the "delete"
        # link can be shown to its author without requiring an account.
        mine = request.session.get('my_comment_ids', [])
        mine.append(comment.id)
        request.session['my_comment_ids'] = mine

        messages.success(
            request,
            get_text('msg.comment_submitted'),
        )
    else:
        messages.error(request, get_text('msg.comment_invalid'))

    return redirect(post.get_absolute_url() + '#comments')


@require_POST
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    mine = request.session.get('my_comment_ids', [])
    owns_it = comment.id in mine or (request.user.is_authenticated and comment.user_id == request.user.id)

    if owns_it or request.user.is_staff:
        post = comment.post
        comment.delete()
        if comment.id in mine:
            mine.remove(comment.id)
            request.session['my_comment_ids'] = mine
        messages.success(request, get_text('msg.comment_deleted'))
        return redirect(post.get_absolute_url() + '#comments')

    messages.error(request, get_text('msg.comment_forbidden'))
    return redirect(comment.post.get_absolute_url() + '#comments')


@require_POST
def like_toggle(request, slug):
    post = get_object_or_404(Post, slug=slug, status=True)

    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    existing = Like.objects.filter(post=post, session_key=session_key).first()
    if existing:
        existing.delete()
        liked = False
    else:
        Like.objects.create(
            post=post,
            session_key=session_key,
            user=request.user if request.user.is_authenticated else None,
        )
        liked = True

    count = post.likes.count()

    if _is_ajax(request):
        return JsonResponse({'liked': liked, 'count': count})
    return redirect(post.get_absolute_url() + '#top')


@login_required
@require_POST
def bookmark_toggle(request, slug):
    post = get_object_or_404(Post, slug=slug, status=True)

    existing = Bookmark.objects.filter(user=request.user, post=post).first()
    if existing:
        existing.delete()
        saved = False
        messages.success(request, get_text('msg.bookmark_removed'))
    else:
        Bookmark.objects.create(user=request.user, post=post)
        saved = True
        messages.success(request, get_text('msg.bookmark_saved'))

    if _is_ajax(request):
        return JsonResponse({'saved': saved})
    return redirect(post.get_absolute_url() + '#top')


# ---------------------------------------------------------------------------
# Accounts — register, profile dashboard + edit, password recovery.
# (login/logout use Django's built-in auth views, wired up in config/urls.py,
# but authenticate via our EmailBackend — see auth_backends.py.)
# ---------------------------------------------------------------------------
def register(request):
    if request.user.is_authenticated:
        return redirect('portfolio:profile_dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user, backend='portfolio.auth_backends.EmailBackend')
            messages.success(request, get_text('msg.welcome', email=user.email))
            return redirect('portfolio:profile_dashboard')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


def _style_nb_form(form):
    """Django's built-in PasswordChangeForm/SetPasswordForm don't know about
    the site's `nb-input` class — add it so they look like the rest of the
    account pages instead of falling back to unstyled browser inputs."""
    for field in form.fields.values():
        existing = field.widget.attrs.get('class', '')
        field.widget.attrs['class'] = f'{existing} nb-input'.strip()
    return form


def _profile_dashboard_context(request, *, profile_form=None, password_form=None, security_form=None):
    """Shared context builder for the dashboard. Accepts an already-bound
    (and possibly invalid) form for whichever section just submitted, so a
    validation error re-renders the full dashboard WITH that form's actual
    field errors still attached — instead of redirecting and silently
    losing them behind a generic "there was an error" message."""
    bookmarks = (
        Bookmark.objects.filter(user=request.user)
        .select_related('post')
        .order_by('-created_at')
    )
    liked_posts = Post.objects.filter(likes__user=request.user).distinct()
    my_comments = (
        Comment.objects.filter(user=request.user)
        .select_related('post')
        .order_by('-created_at')
    )
    security, _ = SecurityCredential.objects.get_or_create(
        user=request.user, defaults={'question': '', 'answer_hash': ''},
    )
    return {
        'bookmarks': bookmarks,
        'liked_posts': liked_posts,
        'my_comments': my_comments,
        'profile_form': profile_form or ProfileEditForm(instance=request.user),
        'password_form': _style_nb_form(password_form or PasswordChangeForm(user=request.user)),
        'security_form': security_form or SecurityQuestionEditForm(instance=security),
        'has_security_question': bool(security.question),
    }


@login_required
def profile_dashboard(request):
    return render(request, 'registration/profile_dashboard.html', _profile_dashboard_context(request))


@login_required
@require_POST
def profile_edit(request):
    # Always bound to request.user — there is no path for a user id to
    # reach this view, so nobody can edit another account through it.
    form = ProfileEditForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, get_text('msg.profile_updated'))
        return redirect('portfolio:profile_dashboard')

    messages.error(request, get_text('msg.fix_errors'))
    context = _profile_dashboard_context(request, profile_form=form)
    return render(request, 'registration/profile_dashboard.html', context)


@login_required
@require_POST
def profile_password_change(request):
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # keep the user logged in
        messages.success(request, get_text('msg.password_changed'))
        return redirect('portfolio:profile_dashboard')

    messages.error(request, get_text('msg.fix_errors'))
    context = _profile_dashboard_context(request, password_form=form)
    return render(request, 'registration/profile_dashboard.html', context)


@login_required
@require_POST
def profile_security_edit(request):
    security, _ = SecurityCredential.objects.get_or_create(
        user=request.user, defaults={'question': '', 'answer_hash': ''},
    )
    form = SecurityQuestionEditForm(request.POST, instance=security)
    if form.is_valid():
        form.save()
        messages.success(request, get_text('msg.security_updated'))
        return redirect('portfolio:profile_dashboard')

    messages.error(request, get_text('msg.fix_errors'))
    context = _profile_dashboard_context(request, security_form=form)
    return render(request, 'registration/profile_dashboard.html', context)


# ---------------------------------------------------------------------------
# Password recovery — security question only, no email sending. A 3-step,
# session-backed flow: identify by email -> answer the question -> set a
# new password. Nothing but the user's own session ever says *which*
# account is being recovered, so there's no id/token in the URL that
# could be edited to target someone else's account.
# ---------------------------------------------------------------------------
def recover_step1(request):
    if request.method == 'POST':
        form = RecoverIdentifyForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip()
            user = User.objects.filter(email__iexact=email).first()
            has_question = user and SecurityCredential.objects.filter(user=user, question__gt='').exists()
            if has_question:
                request.session['recovery_user_id'] = user.id
                request.session.pop('recovery_verified', None)
                return redirect('portfolio:recover_step2')
            messages.error(request, get_text('msg.recover_not_found'))
    else:
        form = RecoverIdentifyForm()

    return render(request, 'registration/recover_step1.html', {'form': form})


def recover_step2(request):
    user_id = request.session.get('recovery_user_id')
    if not user_id:
        return redirect('portfolio:recover_step1')
    security = get_object_or_404(SecurityCredential, user_id=user_id)

    if request.method == 'POST':
        form = RecoverAnswerForm(request.POST)
        if form.is_valid():
            if security.check_answer(form.cleaned_data['answer']):
                request.session['recovery_verified'] = True
                return redirect('portfolio:recover_step3')
            messages.error(request, get_text('msg.recover_wrong_answer'))
    else:
        form = RecoverAnswerForm()

    return render(request, 'registration/recover_step2.html', {'form': form, 'question': security.question})


def recover_step3(request):
    user_id = request.session.get('recovery_user_id')
    if not user_id or not request.session.get('recovery_verified'):
        return redirect('portfolio:recover_step1')
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = SetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            del request.session['recovery_user_id']
            del request.session['recovery_verified']
            messages.success(request, get_text('msg.password_reset_done'))
            return redirect('login')
    else:
        form = SetPasswordForm(user=user)

    return render(request, 'registration/recover_step3.html', {'form': form})


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
            messages.success(request, get_text('msg.contact_sent'))
            return redirect('portfolio:contact')
        messages.error(request, get_text('msg.contact_invalid'))
    else:
        form = ContactForm()

    context = {'form': form}
    return render(request, 'portfolio/contact.html', context)
