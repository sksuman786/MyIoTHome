"""
Serializers for user authentication and profile management.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User, APIKey, LoginLog
import secrets
import string


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'profile_image', 'bio', 'theme',
            'is_email_verified', 'is_active_user', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_email_verified']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for User model."""
    api_keys_count = serializers.SerializerMethodField()
    devices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'profile_image', 'bio', 'theme',
            'is_email_verified', 'email_verified_at', 'is_active_user',
            'two_factor_enabled', 'last_login_ip', 'last_login_device',
            'api_keys_count', 'devices_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_api_keys_count(self, obj):
        return obj.api_keys.filter(is_active=True).count()
    
    def get_devices_count(self, obj):
        return obj.devices.filter(is_active=True).count()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already registered.")
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            # Create account as inactive — admin will manually activate known users
            is_active=False,
        )
        user.get_or_create_api_key(name='Default Device API Key')
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email_or_username = data['email']
        password = data['password']
        user = authenticate(username=email_or_username, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email__iexact=email_or_username)
            except User.DoesNotExist:
                user = None
            else:
                user = authenticate(username=user_obj.username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("New passwords do not match.")
        return data


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for API Key model."""
    
    class Meta:
        model = APIKey
        fields = [
            'id', 'key', 'name', 'is_active', 'can_read_devices',
            'can_write_devices', 'can_read_data', 'can_write_data',
            'rate_limit', 'last_used_at', 'last_used_ip', 'created_at', 'expired_at'
        ]
        read_only_fields = ['id', 'key', 'last_used_at', 'last_used_ip', 'created_at']


class APIKeyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating API Keys."""
    
    class Meta:
        model = APIKey
        fields = ['name', 'can_read_devices', 'can_write_devices', 'can_read_data', 'can_write_data', 'rate_limit']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Generate random key
        key = self.generate_key()
        while APIKey.objects.filter(key=key).exists():
            key = self.generate_key()
        validated_data['key'] = key
        return super().create(validated_data)
    
    @staticmethod
    def generate_key():
        """Generate a random API key."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(40))


class LoginLogSerializer(serializers.ModelSerializer):
    """Serializer for login logs."""
    
    class Meta:
        model = LoginLog
        fields = ['id', 'ip_address', 'device_type', 'browser', 'is_successful', 'created_at']
        read_only_fields = ['id', 'created_at']
