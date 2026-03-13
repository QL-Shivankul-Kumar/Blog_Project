from django.db import models
from django.conf import settings          # ← used for AUTH_USER_MODEL
from django.utils import timezone
from django.utils.text import slugify
from users.models import TimestampMixin   # ← import shared mixin from users
from django.db.models import Count

class TopicManager(models.Manager):
    def with_blog_count(self):
        return self.annotate(
            blog_count=Count('blogs', filter=models.Q(blogs__is_published=True))
        )

    def get_with_blogs(self, topic_id):
        from .models import Blog # here i locally inport it because of any error happen while using blog db call when it not make
        return self.prefetch_related(
            models.Prefetch(
                'blogs',
                queryset=Blog.objects.filter(is_published=True).select_related('author')
            )
        ).get(id=topic_id)

class Topic(TimestampMixin):
    name       = models.CharField(max_length=150, unique=True)
    slug       = models.SlugField(max_length=150, unique=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,      # ← 'users.User' resolved at runtime
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_topics'
    )

    objects = TopicManager()

    class Meta:
        db_table = 'topics'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class BlogManager(models.Manager):

    def published(self):
        return self.filter(is_published=True)

    def by_author(self, author_id):
        return self.filter(author_id=author_id)

    def published_by_author(self, author_id):
        return self.filter(author_id=author_id, is_published=True)

    def search_by_title(self, query):
        return self.filter(is_published=True, title__icontains=query)

    def generate_unique_slug(self, title):
        base = slugify(title)
        slug = base
        n = 1
        while self.filter(slug=slug).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug

class Blog(TimestampMixin):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,      # ← 'users.User' — no circular import
        on_delete=models.SET_NULL,
        null=True,
        related_name='blogs'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.RESTRICT,     # block deletion if blogs exist under topic
        related_name='blogs',
        null=True,
        blank=True
    )
    title        = models.CharField(max_length=255)
    content      = models.TextField()
    banner_image = models.ImageField(upload_to='banners/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    slug         = models.SlugField(max_length=300, unique=True, blank=True)
    view_count   = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = BlogManager()

    class Meta:
        db_table = 'blogs'
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return f"{self.title} ({'Published' if self.is_published else 'Draft'})"

    def publish(self):
        self.is_published = True
        if not self.published_at:
            self.published_at = timezone.now()

    def unpublish(self):
        self.is_published = False

    def increment_view(self):
        """
        Atomic view count increment. F() runs in SQL, not Python.
        Prevents race condition where two requests read the same value simultaneously.
        """
        Blog.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)

class CommentManager(models.Manager):

    def active(self):
        return self.filter(is_deleted=False)

    def for_blog(self, blog_id):
        return self.active().filter(blog_id=blog_id).select_related('user').order_by('created_at')

class Comment(TimestampMixin):
    blog    = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='comments'
    )
    content    = models.TextField()
    is_deleted = models.BooleanField(default=False)

    objects = CommentManager()

    class Meta:
        db_table = 'comments'
        ordering = ['created_at']

    def __str__(self):
        username = self.user.username if self.user else "Deleted User"
        return f"Comment by {username} on '{self.blog.title}'"

    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])
