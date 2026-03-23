from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import PasswordResetToken, Subscription

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'confirm_password']

    def validate(self, data):
        errors = {}

        if User.objects.filter(email=data['email'].lower()).exists():
            errors['email'] = "An account with this email already exists."

        if User.objects.filter(username=data['username']).exists():
            errors['username'] = "This username is already taken."

        if data['password'] != data['confirm_password']:
            errors['confirm_password'] = "Passwords do not match."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data['email'] = validated_data['email'].lower()
        validated_data['role']  = User.Role.READER
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        errors = {}

        user = User.objects.authenticate_user(data['email'], data['password'])
        if not user:
            errors['non_field_errors'] = "Invalid email or password."
        elif not user.is_active:
            errors['non_field_errors'] = "This account has been deactivated."

        if errors:
            raise serializers.ValidationError(errors)

        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password         = serializers.CharField(write_only=True)
    new_password         = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        errors = {}
        user   = self.context['request'].user

        if not user.check_password(data['old_password']):
            errors['old_password'] = "Current password is incorrect."

        if data['new_password'] != data['confirm_new_password']:
            errors['confirm_new_password'] = "New passwords do not match."

        if 'old_password' not in errors and data['old_password'] == data['new_password']:
            errors['new_password'] = "New password must differ from the current one."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    def validate(self, data):
        data['email'] = data['email'].lower()
        return data


class ResetPasswordSerializer(serializers.Serializer):
    token            = serializers.UUIDField()
    new_password     = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        errors = {}

        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(token=data['token'])
            if reset_token.is_used or timezone.now() >= reset_token.expires_at:
                errors['token'] = "This reset link has expired or already been used."
            else:
                self._reset_token = reset_token
        except PasswordResetToken.DoesNotExist:
            errors['token'] = "Invalid or expired reset link."

        if data['new_password'] != data['confirm_password']:
            errors['confirm_password'] = "Passwords do not match."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def save(self):
        user = self._reset_token.user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        return user


class ChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Role.choices)

    def validate(self, data):
        errors = {}

        if self.instance and self.instance.is_superuser:
            errors['role'] = "Superuser role cannot be changed via the API."
            
        if data.get('role') == User.Role.ADMIN:
            errors['role'] = "Cannot assign admin role via the API."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def save(self):
        role = self.validated_data['role']
        self.instance.role         = role
        self.instance.is_staff     = role == 'admin'
        self.instance.is_superuser = False
        self.instance.save(update_fields=['role', 'is_staff', 'is_superuser'])
        return self.instance


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'bio', 'profile_pic', 'role']
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'role', 'bio', 'profile_pic', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'created_at']

    def validate(self, data):
        errors   = {}
        username = data.get('username')

        if username:
            qs = User.objects.filter(username=username)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                errors['username'] = "This username is already taken."

        if errors:
            raise serializers.ValidationError(errors)

        return data


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'role', 'bio', 'profile_pic', 'is_active', 'is_staff',
                  'created_at', 'updated_at']
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    subscriber = UserPublicSerializer(read_only=True)
    author     = UserPublicSerializer(read_only=True)

    class Meta:
        model  = Subscription
        fields = ['id', 'subscriber', 'author', 'subscribed_at']
        read_only_fields = fields