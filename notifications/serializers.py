from rest_framework import serializers
from notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'device',
            'appliance', 'is_read', 'read_at', 'action_url', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for Notification Preferences."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'device_offline_in_app', 'device_online_in_app', 'firmware_update_in_app',
            'appliance_control_in_app', 'device_offline_email', 'device_online_email',
            'firmware_update_email', 'appliance_control_email', 'email_frequency',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end'
        ]
