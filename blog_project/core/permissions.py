from rest_framework.permissions import BasePermission, SAFE_METHODS
from core.constants.messages import PermissionMessages


class IsAdminUser(BasePermission):
    message = PermissionMessages.ADMIN_ONLY

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'admin' or request.user.is_superuser)
        )


class IsAuthor(BasePermission):
    message = PermissionMessages.AUTHOR_ONLY

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'author'
        )


class IsAuthorOrAdmin(BasePermission):
    message = PermissionMessages.AUTHOR_OR_ADMIN

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'author')
        )


class IsOwnerOrAdmin(BasePermission):
    message = PermissionMessages.OWNER_OR_ADMIN

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        if hasattr(obj, 'author'):
            return obj.author == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user