from django.contrib import admin
from accounts.models import User, APIKey, PasswordResetToken, LoginLog


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_email_verified', 'created_at')
    list_filter = ('role', 'is_active', 'is_email_verified', 'theme')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'key', 'is_active', 'last_used_at', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'key', 'user__username')
    readonly_fields = ('id', 'key', 'created_at', 'updated_at', 'last_used_at')



@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at')
    readonly_fields = ('id', 'token', 'created_at')


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'device_type', 'is_successful', 'created_at')
    list_filter = ('is_successful', 'created_at')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('id', 'created_at')
