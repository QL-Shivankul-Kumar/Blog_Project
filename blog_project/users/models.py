from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import uuid
from django.core.exceptions import ValidationError

class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        email = self.normalize_email(email)       # lowercases domain part
        user  = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)               # hashes password — NEVER store plain text
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, username, password, **extra_fields)

    def get_by_email(self, email):
        """Fetch one active user by email. Used in login + forgot-password."""
        return self.get(email=email.lower(), is_active=True)

    def get_all_users(self, role=None):
        """List all active users. Optional role filter. Used in GET /api/users/"""
        qs = self.filter(is_active=True)
        if role:
            qs = qs.filter(role=role)
        return qs

    def get_authors(self):
        return self.filter(role='author', is_active=True)


class User(AbstractBaseUser, PermissionsMixin, TimestampMixin):

    class Role(models.TextChoices):
        READER = 'reader', 'Reader'
        AUTHOR = 'author', 'Author'
        ADMIN = 'admin' , 'Admin'

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name  = models.CharField(max_length=100, blank=True)
    last_name   = models.CharField(max_length=100, blank=True)
    role        = models.CharField(max_length=10, choices=Role.choices, default=Role.READER)
    is_active   = models.BooleanField(default=True)   # False = soft-banned
    is_staff    = models.BooleanField(default=False)  # True = can access /admin/
    bio         = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def is_author(self):
        return self.role == self.Role.AUTHOR
    
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser
    
    def has_perm(self, perm, obj=None):
        if self.is_active and self.is_superuser:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_active and self.is_superuser:
            return True
        return super().has_module_perms(app_label)

class PasswordResetToken(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_tokens'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Valid only if not used AND not expired."""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_used(self):
        # better for the partial updatee save
        self.is_used = True
        self.save(update_fields=['is_used'])

    def __str__(self):
        return f"ResetToken({self.user.email}, used={self.is_used})"

class SubscriptionManager(models.Manager):

    def get_user_subscriptions(self, user):
        return self.filter(subscriber=user).select_related('author')

    def get_author_subscribers(self, author):
        return self.filter(author=author).select_related('subscriber')

    def is_subscribed(self, subscriber, author):
        return self.filter(subscriber=subscriber, author=author).exists()

    def get_subscriber_emails(self, author):
        """
        Flat list of subscriber emails — used when notifying on blog publish.
        flat=True returns ['a@b.com', 'c@d.com'] not [('a@b.com',), ...]
        """
        return list(
            self.filter(author=author)
            .values_list('subscriber__email', flat=True)
        )

class Subscription(models.Model):
    """
    Junction table: User (subscriber) ↔ User (author).
    Lives in users/ — purely about the relationship between two users.
    No reference to Blog or Topic at all.

    unique_together → prevents duplicate subscriptions → prevents spam emails
    clean()         → prevents self-subscription
    """
    subscriber    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    author        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')
    subscribed_at = models.DateTimeField(auto_now_add=True)

    objects = SubscriptionManager()

    class Meta:
        db_table        = 'subscriptions'
        unique_together = ('subscriber', 'author')

    def clean(self):
        if self.subscriber_id == self.author_id:
            raise ValidationError("You cannot subscribe to yourself.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subscriber.username} → {self.author.username}"