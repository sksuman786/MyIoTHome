from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import URLValidator
import uuid
import secrets
import string


class User(AbstractUser):
    """
    Custom User model with additional fields for IoT platform.
    """
    USER_ROLES = (
        ('admin', 'Administrator'),
        ('user', 'Regular User'),
    )
    
    THEME_CHOICES = (
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=10, choices=USER_ROLES, default='user')
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    
    # Account status
    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_active_user = models.BooleanField(default=True)
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else self.username
    
    def is_admin_user(self):
        return self.role == 'admin' or self.is_staff

    def get_or_create_api_key(self, name='Default Device API Key'):
        """Return the first active API key for the user, or create one if missing."""
        api_key = self.api_keys.filter(is_active=True).order_by('created_at').first()
        if api_key:
            return api_key
        return APIKey.objects.create(
            user=self,
            name=name,
            key=APIKey.generate_key(),
            can_read_devices=True,
            can_write_devices=True,
            can_read_data=True,
            can_write_data=True
        )


class APIKey(models.Model):
    """
    API Keys for device authentication and user API access.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=40, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    
    # Permissions
    can_read_devices = models.BooleanField(default=True)
    can_write_devices = models.BooleanField(default=True)
    can_read_data = models.BooleanField(default=True)
    can_write_data = models.BooleanField(default=True)
    
    # Rate limiting
    rate_limit = models.IntegerField(default=1000, help_text="Requests per hour")
    
    # Tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
    
    def __str__(self):
        return f"{self.name} - {self.key[:8]}..."

    @staticmethod
    def generate_key():
        alphabet = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(alphabet) for _ in range(40))
        while APIKey.objects.filter(key=key).exists():
            key = ''.join(secrets.choice(alphabet) for _ in range(40))
        return key
    
    def is_valid(self):
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.expired_at and self.expired_at < timezone.now():
            return False
        return True



class PasswordResetToken(models.Model):
    """
    Password reset tokens for forgotten passwords.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()


class LoginLog(models.Model):
    """
    Log user login attempts and IP addresses.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    is_successful = models.BooleanField(default=True)
    failed_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Login Log'
        verbose_name_plural = 'Login Logs'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
