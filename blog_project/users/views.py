from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import User, PasswordResetToken, Subscription
from .serializers import (
    RegisterSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, ChangePasswordSerializer,
    UserPublicSerializer, UserProfileSerializer, UserAdminSerializer,
    SubscriptionSerializer,ChangeRoleSerializer
)
from .permissions import IsAdminUser, IsAuthorOrAdmin
from .utils import success_response, error_response, get_tokens_for_user, send_reset_email_async
from django.contrib.auth import get_user_model

# this will create the user model here to dirctly talk to db
User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Registration failed.", serializer.errors, status.HTTP_400_BAD_REQUEST)
        user   = serializer.save()
        tokens = get_tokens_for_user(user)
        return success_response(
            data={**UserProfileSerializer(user).data, **tokens},
            message="Registration successful.",
            status_code=status.HTTP_201_CREATED
        )
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response("Login failed.", serializer.errors, status.HTTP_401_UNAUTHORIZED)
        user   = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        return success_response(
            data={**UserProfileSerializer(user).data, **tokens},
            message="Login successful."
        )

class ChangeRoleView(APIView):
    """
    PATCH /api/users/:id/role/
    permission: IsAdminUser — only admins can call this
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk, is_active=True)

        # Admin cannot change their own role via API (safety guard)
        if user == request.user:
            return error_response(
                "You cannot change your own role.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer = ChangeRoleSerializer(
            instance=user,
            data=request.data
        )
        if not serializer.is_valid():
            return error_response("Role change failed.", serializer.errors)

        serializer.save()
        user.refresh_from_db()
        return success_response(
            data=UserAdminSerializer(user).data,
            message=f"{user.username}'s role changed to '{user.role}'."
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return error_response("refresh_token is required.")
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(message="Logged out successfully.")
        except TokenError as e:
            return error_response(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return error_response("refresh_token is required.")
        try:
            old_token = RefreshToken(refresh_token)
            user_id = old_token['user_id']
            user = User.objects.get(id=user_id)
            old_token.blacklist()
            token = RefreshToken.for_user(user)
            return success_response(data={'access_token': str(token.access_token), 'refresh_token' : str(token)})
        except TokenError:
            return error_response("Invalid or expired refresh token.", status_code=status.HTTP_401_UNAUTHORIZED)
        

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Invalid request.", serializer.errors)

        SAFE_MSG = "If an account with this email exists, a reset link has been sent."
        email = serializer.validated_data['email']

        try:
            user = User.objects.get_by_email(email)
        except User.DoesNotExist:
            return success_response(message=SAFE_MSG)

        # Invalidate previous tokens, create fresh one
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        reset_token  = PasswordResetToken.objects.create(user=user)
        # frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"http://localhost:8000/api/auth/reset-password?token={reset_token.token}"
        print(reset_link)
        # send_reset_email_async(user.email, user.username, reset_link)
        return success_response(message=SAFE_MSG)
    
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Password reset failed.", serializer.errors)
        serializer.save()
        return success_response(message="Password reset successful. You can now log in.")
    
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response("Password change failed.", serializer.errors)
        serializer.save()
        return success_response(message="Password changed. Please log in again.")

class UserListView(APIView):
    """admin only thing this"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        role  = request.query_params.get('role')
        users = User.objects.get_all_users(role=role)
        serializer = UserAdminSerializer(users,many=True)
        return success_response(data=serializer.data)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(data=UserProfileSerializer(request.user).data)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(User, pk=pk, is_active=True)

    def get(self, request, pk):
        user = self.get_object(pk)
        if request.user.is_admin_user():
            serializer = UserAdminSerializer(user)
        elif  request.user.pk == user.pk:
            serializer = UserProfileSerializer(user)
        else:
            serializer = UserPublicSerializer(user)
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        user = self.get_object(pk)
        if not (request.user == user or request.user.is_admin_user()):
            return error_response("You can only update your own account.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Update failed.", serializer.errors)
        serializer.save()
        return success_response(data=serializer.data, message="Profile updated.")

    def delete(self, request, pk):
        user = self.get_object(pk)
        if not (request.user == user or request.user.is_admin_user()):
            return error_response("You can only delete your own account.", status_code=status.HTTP_403_FORBIDDEN)
        # user.is_active = False
        # user.email = f"deleted_{user.pk}_{user.email}"  # free up the email
        # user.save(update_fields=['is_active', 'email'])
        user.delete()
        return success_response(message="Account deleted.", status_code=status.HTTP_204_NO_CONTENT)

class MySubscriptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subs = Subscription.objects.get_user_subscriptions(request.user)
        return success_response(data=SubscriptionSerializer(subs, many=True).data)

class AuthorSubscribersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id):
        author = get_object_or_404(User, pk=author_id, role=User.Role.AUTHOR)
        subs   = Subscription.objects.get_author_subscribers(author)
        return success_response(data=SubscriptionSerializer(subs, many=True).data)
    

class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def get_author(self, author_id):
        return get_object_or_404(User, pk=author_id, role=User.Role.AUTHOR)

    def post(self, request, author_id):
        author = self.get_author(author_id)
        if request.user.pk == author.pk:
            return error_response("You cannot subscribe to yourself.", status_code=status.HTTP_400_BAD_REQUEST)
        if Subscription.objects.is_subscribed(request.user, author):
            return error_response("You are already subscribed.", status_code=status.HTTP_400_BAD_REQUEST)
        sub = Subscription.objects.create(subscriber=request.user, author=author)
        return success_response(
            data=SubscriptionSerializer(sub).data,
            message=f"Subscribed to {author.username}.",
            status_code=status.HTTP_201_CREATED
        )

    def delete(self, request, author_id):
        author   = self.get_author(author_id)
        deleted,_ = Subscription.objects.filter(subscriber=request.user, author=author).delete()
        # print(Subscription.objects.filter(subscriber=request.user, author=author))
        # print(deleted)
        if not deleted:
            return error_response("You are not subscribed to this author.", status_code=status.HTTP_404_NOT_FOUND)
        return success_response(message=f"Unsubscribed from {author.username}.")