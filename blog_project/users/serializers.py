from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, PasswordResetToken, Subscription

class RegisterSerializer(serializers.ModelSerializer):

    password         = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name','password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data['role'] = User.Role.READER
        return User.objects.create_user(**validated_data)
    

class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            request=self.context.get('request'),
            username=data['email'], 
            password=data['password']
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")
        data['user'] = user
        return data

class ChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Role.choices)
    def validate_role(self, value):
        # Superuser role cannot be changed via API for safety
        if self.instance and self.instance.is_superuser:
            raise serializers.ValidationError(
                "Superuser role cannot be changed via the API."
            )
        return value

    def save(self):
        role = self.validated_data['role']
        self.instance.role         = role
        self.instance.is_superuser = False  # never via API
        self.instance.is_staff     = True if role == 'admin' else False
        self.instance.save(update_fields=['role', 'is_staff', 'is_superuser'])
        return self.instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password         = serializers.CharField(write_only=True)
    new_password         = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError({"new_password": "New password must differ from current."})
        return data
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length = 255)

    def validate_email(self, value):
        return value.lower()
    

class ResetPasswordSerializer(serializers.Serializer):
    token            = serializers.UUIDField()
    new_password     = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired reset link.")
        if not reset_token.is_valid():
            raise serializers.ValidationError("This reset link has expired or already been used.")
        self._reset_token = reset_token
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def save(self):
        user = self._reset_token.user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        self._reset_token.mark_used()
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        return user
    
class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'first_name', 'last_name', 'bio', 'profile_pic', 'role']
        read_only_fields = fields

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'role', 'bio', 'profile_pic', 'is_active', 'created_at']
        # role is read_only here — cannot be changed via profile update
        read_only_fields = ['id', 'email', 'role', 'is_active', 'created_at']

    def validate_username(self, value):
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
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