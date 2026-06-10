from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Notification(models.Model):
    """
    In-app notifications for users.
    """
    NOTIFICATION_TYPES = (
        ('device_offline', 'Device Offline'),
        ('device_online', 'Device Online'),
        ('firmware_update', 'Firmware Update'),
        ('appliance_control', 'Appliance Control'),
        ('system_alert', 'System Alert'),
        ('info', 'Information'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='info')
    
    # Related objects
    device = models.ForeignKey('devices.Device', on_delete=models.SET_NULL, null=True, blank=True)
    appliance = models.ForeignKey('devices.Appliance', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Action
    action_url = models.CharField(max_length=500, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        from django.utils.timezone import now
        self.is_read = True
        self.read_at = now()
        self.save()


class NotificationPreference(models.Model):
    """
    User notification preferences.
    """
    FREQUENCY_CHOICES = (
        ('immediate', 'Immediate'),
        ('hourly', 'Hourly Digest'),
        ('daily', 'Daily Digest'),
        ('never', 'Never'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    
    # In-app notifications
    device_offline_in_app = models.BooleanField(default=True)
    device_online_in_app = models.BooleanField(default=True)
    firmware_update_in_app = models.BooleanField(default=True)
    appliance_control_in_app = models.BooleanField(default=True)
    
    # Email notifications
    device_offline_email = models.BooleanField(default=True)
    device_online_email = models.BooleanField(default=False)
    firmware_update_email = models.BooleanField(default=True)
    appliance_control_email = models.BooleanField(default=False)
    
    # Frequency
    email_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='immediate')
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
