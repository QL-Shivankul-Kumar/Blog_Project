from django.contrib import admin
from django.utils.html import format_html
from .models import Topic, Blog, Comment

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    """
    Manage blog categories. Slug is auto-generated from name
    in the model's save() so it's read-only here.
    """
    list_display    = ['name', 'slug', 'created_by', 'created_at']
    list_filter     = ['created_at']
    search_fields   = ['name', 'slug']
    ordering        = ['name']
    readonly_fields = ['slug', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display    = ['title', 'author', 'topic', 'status_badge', 'view_count', 'published_at', 'created_at']
    list_filter     = ['is_published', 'topic', 'created_at']
    search_fields   = ['title', 'author__username', 'author__email', 'topic__name']
    ordering        = ['-created_at']
    list_per_page   = 20
    readonly_fields = ['slug', 'view_count', 'published_at', 'created_at', 'updated_at']

    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'content', 'banner_image')
        }),
        ('Meta', {
            'fields': ('author', 'topic', 'is_published', 'published_at')
        }),
        ('Stats', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Status', ordering='is_published')
    def status_badge(self, obj):
        if obj.is_published:
            return format_html(
                '<span style="background:#28a745;color:white;padding:2px 8px;'
                'border-radius:4px;font-size:11px;">Published</span>'
            )
        return format_html(
            '<span style="background:#6c757d;color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">Draft</span>'
        )

    @admin.action(description='Publish selected blogs')
    def publish_blogs(self, request, queryset):
        count = 0
        for blog in queryset.filter(is_published=False):
            blog.publish()   # sets is_published=True and published_at
            blog.save()
            count += 1
        self.message_user(request, f'{count} blog(s) published.')

    @admin.action(description='Unpublish selected blogs')
    def unpublish_blogs(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} blog(s) moved to draft.')

    actions = ['publish_blogs', 'unpublish_blogs']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display    = ['short_content', 'user', 'blog', 'is_deleted', 'created_at']
    list_filter     = ['is_deleted', 'created_at']
    search_fields   = ['content', 'user__username', 'user__email', 'blog__title']
    ordering        = ['-created_at']
    list_per_page   = 30
    readonly_fields = ['user', 'blog', 'created_at', 'updated_at']

    def get_queryset(self, request):
        return Comment._default_manager.all()

    @admin.display(description='Content')
    def short_content(self, obj):
        return obj.content[:60] + '...' if len(obj.content) > 60 else obj.content

    @admin.action(description='Restore selected deleted comments')
    def restore_comments(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f'{updated} comment(s) restored.')

    @admin.action(description='Soft-delete selected comments')
    def soft_delete_comments(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} comment(s) soft-deleted.')

    actions = ['restore_comments', 'soft_delete_comments']