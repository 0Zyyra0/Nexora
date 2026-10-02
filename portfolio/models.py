from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def unique_slugify(instance, value, slug_field_name='slug'):
    """Generate a unique slug for `instance` based on `value`."""
    model = instance.__class__
    base_slug = slugify(value, allow_unicode=True) or 'item'
    slug = base_slug
    n = 1
    qs = model.objects.exclude(pk=instance.pk)
    while qs.filter(**{slug_field_name: slug}).exists():
        n += 1
        slug = f'{base_slug}-{n}'
    return slug


# ---------------------------------------------------------------------------
# Profile ("About me") — a single-row model holding the site owner's info.
# ---------------------------------------------------------------------------
class Profile(models.Model):
    name = models.CharField(max_length=120)
    role = models.CharField(
        max_length=150,
        blank=True,
        help_text='e.g. "Full-Stack Developer & UI Designer"',
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='profile/', blank=True, null=True)
    resume = models.FileField(
        upload_to='profile/resume/', blank=True, null=True,
        help_text='CV / resume file (PDF, etc.)',
    )
    location = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profile'

    def __str__(self):
        return self.name or 'Profile'

    def save(self, *args, **kwargs):
        # Keep this a singleton: always reuse the first row.
        if not self.pk and Profile.objects.exists():
            self.pk = Profile.objects.first().pk
        super().save(*args, **kwargs)


class SocialLink(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='social_links')
    platform = models.CharField(max_length=50, help_text='e.g. GitHub, LinkedIn, Twitter')
    icon_class = models.CharField(
        max_length=50, default='bi-link-45deg',
        help_text='Bootstrap Icons class, e.g. "bi-github", "bi-linkedin"',
    )
    url = models.URLField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.platform}'


class Experience(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=150, help_text='Job title / position')
    organization = models.CharField(max_length=150)
    location = models.CharField(max_length=150, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(
        blank=True, null=True,
        help_text='Leave empty if this is your current position',
    )
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', '-start_date']

    def __str__(self):
        return f'{self.title} @ {self.organization}'

    @property
    def is_current(self):
        return self.end_date is None


class Skill(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    percent = models.PositiveIntegerField(
        default=80, validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', '-percent']

    def __str__(self):
        return f'{self.name} ({self.percent}%)'


# ---------------------------------------------------------------------------
# Shared tags (used by both Project and Post)
# ---------------------------------------------------------------------------
class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Work / portfolio projects
# ---------------------------------------------------------------------------
class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    content = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='projects/covers/', blank=True, null=True)
    client = models.CharField(max_length=150, blank=True)
    project_url = models.URLField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='projects')
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('portfolio:work_detail', kwargs={'slug': self.slug})


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.caption or f'Image for {self.project.title}'


# ---------------------------------------------------------------------------
# Blog posts
# ---------------------------------------------------------------------------
class Post(models.Model):
    class Category(models.TextChoices):
        DESIGN = 'design', 'Design'
        GRAPHIC = 'graphic', 'Graphic'
        MARKETING = 'marketing', 'Marketing'
        FINANCE = 'finance', 'Finance'
        MUSIC = 'music', 'Music'
        EDUCATION = 'education', 'Education'

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.DESIGN)
    excerpt = models.CharField(max_length=300, blank=True)
    content = models.TextField()
    cover_image = models.ImageField(upload_to='posts/covers/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    featured = models.BooleanField(default=False)
    status = models.BooleanField(default=True, help_text='Published?')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('portfolio:blog_detail', kwargs={'slug': self.slug})


# ---------------------------------------------------------------------------
# Standalone gallery
# ---------------------------------------------------------------------------
class GalleryImage(models.Model):
    title = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to='gallery/')
    caption = models.CharField(max_length=250, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f'Gallery image #{self.pk}'


# ---------------------------------------------------------------------------
# Contact form submissions
# ---------------------------------------------------------------------------
class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}> - {self.subject or "(no subject)"}'


# ---------------------------------------------------------------------------
# Blog comments — guest commenting (name + email, no account required),
# single-level replies, and admin moderation (approve/reject/spam).
# ---------------------------------------------------------------------------
class Comment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SPAM = 'spam', 'Spam'

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies',
        help_text='Set automatically when this comment is a reply to another one.',
    )
    # Optional — set automatically when the commenter is logged in, so their
    # own comments can show up on their profile page.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='comments',
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    body = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.name} on {self.post.title}'

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED


# ---------------------------------------------------------------------------
# One like per (post, session) — works for anonymous visitors (via their
# session cookie) and keeps a `user` reference too so logged-in people can
# see their liked articles on their profile page.
# ---------------------------------------------------------------------------
class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        related_name='post_likes',
    )
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'session_key'], name='unique_like_per_session'),
        ]

    def __str__(self):
        return f'Like on {self.post.title}'


# ---------------------------------------------------------------------------
# Saved / bookmarked articles — requires an account.
# ---------------------------------------------------------------------------
class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_bookmark_per_user'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} saved {self.post.title}'


# ---------------------------------------------------------------------------
# Security-question password recovery (no email sending involved). The
# answer is hashed with Django's own password hasher — never stored as
# plain text — and compared case-insensitively.
# ---------------------------------------------------------------------------
class SecurityCredential(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='security')
    question = models.CharField(max_length=255)
    answer_hash = models.CharField(max_length=255)

    def __str__(self):
        return f'Security question for {self.user}'

    def set_answer(self, raw_answer):
        self.answer_hash = make_password(raw_answer.strip().lower())

    def check_answer(self, raw_answer):
        return check_password(raw_answer.strip().lower(), self.answer_hash)
