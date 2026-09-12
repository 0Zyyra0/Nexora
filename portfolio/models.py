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
