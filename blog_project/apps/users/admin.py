from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from .models import User, PasswordResetToken, Subscription


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # ── List view (the table of all users) ───────────────────────────────────
    list_display    = ['username', 'email', 'role', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    list_filter     = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields   = ['username', 'email', 'first_name', 'last_name']
    ordering        = ['-created_at']
    list_per_page   = 25
 
    # ── Detail/Edit view (form for one user) ─────────────────────────────────
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'bio', 'profile_pic')
        }),
        ('Role & Status', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
 
    # Fields shown when CREATING a new user via admin panel
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )
 
    readonly_fields = ['created_at', 'updated_at', 'last_login']
 
    # ── Custom bulk actions ───────────────────────────────────────────────────
 
    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated.')
 
    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.')
 
    @admin.action(description='Promote selected users to Author')
    def make_author(self, request, queryset):
        updated = queryset.update(role=User.Role.AUTHOR)
        self.message_user(request, f'{updated} user(s) promoted to Author.')
 
    @admin.action(description='Demote selected users to Reader')
    def make_reader(self, request, queryset):
        updated = queryset.update(role=User.Role.READER)
        self.message_user(request, f'{updated} user(s) demoted to Reader.')
 
    actions = ['activate_users', 'deactivate_users', 'make_author', 'make_reader']
 

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display    = ['user', 'token', 'is_used', 'is_expired_display', 'created_at', 'expires_at']
    list_filter     = ['is_used', 'created_at']
    search_fields   = ['user__email', 'user__username']
    ordering        = ['-created_at']
    readonly_fields = ['user', 'token', 'created_at', 'expires_at', 'is_used']
 
    def has_add_permission(self, request):
        # Prevent creating tokens manually via admin
        return False
 
    @admin.display(description='Expired?', boolean=True)
    def is_expired_display(self, obj):
        return timezone.now() >= obj.expires_at


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display    = ['subscriber', 'author', 'subscribed_at']
    list_filter     = ['subscribed_at']
    search_fields   = ['subscriber__username', 'subscriber__email',
                       'author__username',     'author__email']
    ordering        = ['-subscribed_at']
    readonly_fields = ['subscriber', 'author', 'subscribed_at']
 
    def has_add_permission(self, request):
        return False