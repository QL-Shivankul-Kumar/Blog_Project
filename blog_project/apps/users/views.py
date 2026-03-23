from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import User, PasswordResetToken, Subscription
from .serializers import (
    RegisterSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, ChangePasswordSerializer,
    UserPublicSerializer, UserProfileSerializer, UserAdminSerializer,
    SubscriptionSerializer, ChangeRoleSerializer,
)
from core.permissions import IsAdminUser
from core.utils.responder import success_response
from core.constants.messages import AuthMessages, UserMessages, SubscriptionMessages
from core.exceptions import (
    AppValidationError, ResourceNotFound,
    CustomPermissionDenied as PermissionDenied, ConflictError,
)
from core.utils.email import send_reset_email_async

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user   = serializer.save()
        tokens = User.objects.generate_tokens(user)
        return success_response(
            data={**UserProfileSerializer(user).data, **tokens},
            message=AuthMessages.REGISTER_SUCCESS,
            status_code=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user   = serializer.validated_data['user']
        tokens = User.objects.generate_tokens(user)
        return success_response(
            data={**UserProfileSerializer(user).data, **tokens},
            message=AuthMessages.LOGIN_SUCCESS,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            raise AppValidationError(AuthMessages.REFRESH_TOKEN_REQUIRED)
        token = RefreshToken(refresh_token)
        token.blacklist()
        return success_response(message=AuthMessages.LOGOUT_SUCCESS)


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw = request.data.get('refresh_token')
        if not raw:
            raise AppValidationError(AuthMessages.REFRESH_TOKEN_REQUIRED)
        tokens = User.objects.rotate_refresh_token(raw)
        return success_response(
            data=tokens,
            message=AuthMessages.TOKEN_REFRESH_SUCCESS,
        )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return success_response(message=AuthMessages.FORGOT_PASSWORD_SAFE)

        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        reset_token = PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        reset_link = f"http://localhost:8000/api/users/password/reset/?token={reset_token.token}"
        print(reset_link)  # remove in production
        send_reset_email_async(user.email, user.username, reset_link)
        return success_response(message=AuthMessages.FORGOT_PASSWORD_SAFE)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message=AuthMessages.PASSWORD_RESET_SUCCESS)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message=AuthMessages.PASSWORD_CHANGE_SUCCESS)


class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        role  = request.query_params.get('role')
        users = User.objects.get_all_users(role=role)
        return success_response(
            data=UserAdminSerializer(users, many=True).data,
            message=UserMessages.LIST_FETCHED,
        )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(
            data=UserProfileSerializer(request.user).data,
            message=UserMessages.PROFILE_FETCHED,
        )


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(User, pk=pk, is_active=True)

    def get(self, request, pk):
        user = self.get_object(pk)
        if request.user.role == 'admin' or request.user.is_superuser:
            serializer = UserAdminSerializer(user)
        elif request.user.pk == user.pk:
            serializer = UserProfileSerializer(user)
        else:
            serializer = UserPublicSerializer(user)
        return success_response(
            data=serializer.data,
            message=UserMessages.DETAIL_FETCHED,
        )

    def patch(self, request, pk):
        user = self.get_object(pk)
        if request.user.pk != user.pk and request.user.role != 'admin':
            raise PermissionDenied(UserMessages.FORBIDDEN)
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data,
            message=UserMessages.PROFILE_UPDATED,
        )

    def delete(self, request, pk):
        user = self.get_object(pk)
        if request.user.pk != user.pk and request.user.role != 'admin':
            raise PermissionDenied(UserMessages.DELETE_FORBIDDEN)
        user.delete()
        return success_response(
            message=UserMessages.ACCOUNT_DELETED,
            status_code=status.HTTP_204_NO_CONTENT,
        )


class ChangeRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk, is_active=True)
        if user == request.user:
            raise AppValidationError(AuthMessages.CANNOT_CHANGE_OWN_ROLE)
        serializer = ChangeRoleSerializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user.refresh_from_db()
        return success_response(
            data=UserAdminSerializer(user).data,
            message=f"{user.username}'s role changed to '{user.role}'.",
        )

class MySubscriptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subs = Subscription.objects.get_user_subscriptions(request.user)
        return success_response(
            data=SubscriptionSerializer(subs, many=True).data,
            message=SubscriptionMessages.MY_SUBS_FETCHED,
        )


class AuthorSubscribersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id):
        author = get_object_or_404(User, pk=author_id, role=User.Role.AUTHOR)
        subs   = Subscription.objects.get_author_subscribers(author)
        return success_response(
            data=SubscriptionSerializer(subs, many=True).data,
            message=SubscriptionMessages.SUBSCRIBERS_FETCHED,
        )


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_author(self, author_id):
        return get_object_or_404(User, pk=author_id, role=User.Role.AUTHOR)

    def post(self, request, author_id):
        author = self._get_author(author_id)
        if request.user.pk == author.pk:
            raise AppValidationError(SubscriptionMessages.SELF_SUBSCRIBE)
        if Subscription.objects.is_subscribed(request.user, author):
            raise ConflictError(SubscriptionMessages.ALREADY_SUBSCRIBED)
        sub = Subscription.objects.create(subscriber=request.user, author=author)
        return success_response(
            data=SubscriptionSerializer(sub).data,
            message=SubscriptionMessages.SUBSCRIBED.format(author=author.username),
            status_code=status.HTTP_201_CREATED,
        )

    def delete(self, request, author_id):
        author     = self._get_author(author_id)
        deleted, _ = Subscription.objects.filter(
            subscriber=request.user, author=author
        ).delete()
        if not deleted:
            raise ResourceNotFound(SubscriptionMessages.NOT_SUBSCRIBED)
        return success_response(
            message=SubscriptionMessages.UNSUBSCRIBED.format(author=author.username),
        )