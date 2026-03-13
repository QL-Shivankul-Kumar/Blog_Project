from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthor(BasePermission):
    message = "Only authors can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_author()
        )


class IsAdminUser(BasePermission):
    message = "Only admins can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin_user()
        )


class IsOwnerOrAdmin(BasePermission):
    message = "You can only modify your own content."

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_user():
            return True
        if hasattr(obj, 'author'):
            return obj.author == request.user
        if hasattr(obj, 'user') and hasattr(obj, 'blog'):
            return obj.user == request.user
        if hasattr(obj, 'email') and hasattr(obj, 'username'):
            return obj == request.user
        return False


class IsAuthorOrAdmin(BasePermission):
    message = "Only authors or admins can perform this action."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_author() or request.user.is_admin_user())
        )