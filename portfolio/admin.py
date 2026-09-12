from django.contrib import admin

from .models import (
    ContactMessage,
    Experience,
    GalleryImage,
    Post,
    Profile,
    Project,
    ProjectImage,
    Skill,
    SocialLink,
    Tag,
)


class SocialLinkInline(admin.TabularInline):
    model = SocialLink
    extra = 1


class ExperienceInline(admin.StackedInline):
    model = Experience
    extra = 0


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    inlines = [SocialLinkInline, ExperienceInline, SkillInline]
    list_display = ('name', 'role', 'email', 'location', 'updated_at')

    def has_add_permission(self, request):
        # Enforce a single Profile row from the admin UI.
        if Profile.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [ProjectImageInline]
    list_display = ('title', 'client', 'featured', 'order', 'created_at')
    list_filter = ('featured', 'tags')
    search_fields = ('title', 'short_description', 'content', 'client')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'featured', 'status', 'created_at')
    list_filter = ('category', 'featured', 'status', 'tags')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    date_hierarchy = 'created_at'


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'created_at')
    ordering = ('order', '-created_at')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
