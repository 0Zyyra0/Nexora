from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import DatabaseError, models
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


# ---------------------------------------------------------------------------
# Site settings — a single-row model holding all editable page text
# (headings, intros, buttons, taglines) so it can be changed from the admin.
# ---------------------------------------------------------------------------
def _text(default, max_length=255):
    return models.CharField(max_length=max_length, default=default, blank=True)


class SiteSettings(models.Model):
    # Global / header / footer
    tagline = _text('Portfolio & blog')
    meta_description = _text('Personal portfolio & blog')
    nav_cta = _text('Get in touch')
    footer_explore_title = _text('Explore')
    footer_contact_title = _text('Say hello')
    footer_social_title = _text('Elsewhere')
    footer_copyright = _text('All rights reserved.')

    # Home
    home_hero_fallback_title = _text("Hi, I'm a creative")
    home_hero_fallback_intro = _text('Welcome to my portfolio and blog.')
    home_hero_primary_button = _text('See the work')
    home_hero_secondary_button = _text('Get in touch')
    home_work_eyebrow = _text('Selected work')
    home_work_title = _text('Recent projects')
    home_work_lead = _text('A few favourites — open any project for the full write-up.')
    home_work_link = _text('All projects')
    home_blog_eyebrow = _text('From the blog')
    home_blog_title = _text('Recent writing')
    home_blog_link = _text('All posts')
    home_about_eyebrow = _text('About')
    home_about_fallback_title = _text('A bit about me')
    home_about_link = _text('More about me')
    cta_title = _text("Got a project? Let's talk.")
    cta_text = _text("Tell me what you need and I'll get back to you shortly.")
    cta_button = _text('Get in touch')
    cta_email_button = _text('Email me')

    # About
    about_title = _text('About')
    about_resume_button = _text('Download resume')
    about_skills_title = _text('Skills')
    about_experience_eyebrow = _text('Experience')
    about_experience_title = _text("Where I've worked")

    # Work
    work_title = _text('Work')
    work_intro = _text('Case studies and projects, open any one for the full write-up.')
    work_related_title = _text('Related projects')

    # Blog
    blog_title = _text('Blog')
    blog_intro = _text("Writing on things I'm working on.")
    blog_comment_form_title = _text('Leave a comment')
    blog_comment_form_note = _text('Comments are shown after approval.')

    # Gallery
    gallery_title = _text('Gallery')
    gallery_intro = _text('A few extra pictures.')

    # Contact
    contact_title = _text('Contact')
    contact_intro = _text("Tell me a bit about what you need — I'll get back to you shortly.")
    contact_details_title = _text('Other ways to reach me')
    contact_submit_button = _text('Send message')

    # Account pages
    login_tag = _text('Members only')
    login_title = _text('Log in.')
    login_subtitle = _text('No fluff. Just your inbox and your work.')
    register_tag = _text('New here?')
    register_title = _text('Create an account.')
    register_subtitle = _text('Save articles, like posts, and keep track of your comments.')
    logged_out_tag = _text('See you soon')
    logged_out_title = _text('Logged out.')
    logged_out_subtitle = _text("You've been signed out of your account.")
    dashboard_title = _text('My account.')
    recover_tag = _text('Account recovery')
    recover_title = _text('Forgot your password?')
    recover_subtitle = _text('No email needed — just answer your security question.')
    recover_question_tag = _text('Step 2 of 3')
    recover_question_subtitle = _text("Answer exactly as you set it up — it's not case-sensitive.")
    recover_reset_tag = _text('Step 3 of 3')
    recover_reset_title = _text('Choose a new password.')
    recover_reset_subtitle = _text('Verified — set a new password to finish.')

    # 404 page
    not_found_badge = _text('OOPS.')
    not_found_title = _text('This page ghosted you.')
    not_found_text = _text("We looked everywhere. Behind the couch. In the junk drawer. It's gone.")
    not_found_button = _text('Take me home →')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site settings'
        verbose_name_plural = 'Site settings'

    def __str__(self):
        return 'Site settings'

    def save(self, *args, **kwargs):
        # Keep this a singleton: always reuse the first row.
        if not self.pk and SiteSettings.objects.exists():
            self.pk = SiteSettings.objects.first().pk
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Return the saved settings, or an unsaved instance with the defaults."""
        try:
            return cls.objects.first() or cls()
        except DatabaseError:
            # Table missing (migrations not applied yet) — fall back to defaults.
            return cls()
