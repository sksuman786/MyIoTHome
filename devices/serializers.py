"""
Serializers for devices and appliances.
"""

from rest_framework import serializers
from devices.models import (
    Device, Appliance, ApplianceHistory, DeviceData, DeviceFirmware,
    WaterMonitoringData, WaterPumpTimer, OTAUpdate
)


class ApplianceSerializer(serializers.ModelSerializer):
    """Serializer for Appliance model."""
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    
    class Meta:
        model = Appliance
        fields = [
            'id', 'device', 'name', 'description', 'appliance_type', 'pin', 'virtual_pin',
            'state', 'state_display', 'value', 'icon', 'room', 'power_consumption', 'can_control',
            'is_active', 'created_at', 'updated_at', 'last_updated', 'last_state_change'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_updated', 'last_state_change']


class ApplianceHistorySerializer(serializers.ModelSerializer):
    """Serializer for Appliance History."""
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    triggered_by_display = serializers.CharField(source='get_triggered_by_display', read_only=True)
    
    class Meta:
        model = ApplianceHistory
        fields = [
            'id', 'appliance', 'previous_state', 'new_state', 'action', 'action_display',
            'triggered_by', 'triggered_by_display', 'triggered_by_user', 'timestamp', 'duration'
        ]
        read_only_fields = ['id', 'timestamp']


class DeviceDataSerializer(serializers.ModelSerializer):
    """Serializer for Device Data logs."""
    
    class Meta:
        model = DeviceData
        fields = [
            'id', 'device', 'wifi_signal',
            'wifi_quality', 'uptime', 'free_memory', 'power_consumption', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class DeviceFirmwareSerializer(serializers.ModelSerializer):
    """Serializer for Device Firmware."""
    
    class Meta:
        model = DeviceFirmware
        fields = [
            'id', 'version', 'device_type', 'file', 'file_size', 'checksum',
            'changelog', 'release_notes', 'status', 'created_at', 'released_at', 'deprecated_at'
        ]
        read_only_fields = ['id', 'file_size', 'checksum', 'created_at']


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    appliances_count = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'user', 'device_id', 'device_name', 'device_type', 'device_role', 'status', 'status_display',
            'firmware_version', 'mac_address', 'ip_address',
            'wifi_signal', 'is_active', 'timezone', 'location', 'description',
            'created_at', 'updated_at', 'last_seen', 'last_heartbeat',
            'appliances_count', 'is_online'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_seen', 'last_heartbeat',
            'is_online', 'status'
        ]
    
    def get_appliances_count(self, obj):
        return obj.appliances.filter(is_active=True).count()
    
    def get_is_online(self, obj):
        return obj.is_online()


class DeviceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Device with appliances."""
    appliances = ApplianceSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'user', 'device_id', 'device_name', 'device_type', 'device_role', 'status',
            'status_display', 'firmware_version', 'mac_address', 'ip_address', 'wifi_signal', 'is_active', 'timezone', 'location', 'description',
            'created_at', 'updated_at', 'last_seen', 'last_heartbeat', 'appliances', 'is_online'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_online']
    
    def get_is_online(self, obj):
        return obj.is_online()


class DeviceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating devices."""
    
    class Meta:
        model = Device
        fields = [
            'device_id', 'device_name', 'device_type', 'device_role', 'firmware_version',
            'mac_address', 'timezone', 'location', 'description'
        ]


class ApplianceToggleSerializer(serializers.Serializer):
    """Serializer for toggling appliance state or setting numeric value."""
    state = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=1)
    value = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=255)
    
    def validate(self, data):
        # Either state or value must be provided
        if data.get('state') is None and data.get('value') is None:
            raise serializers.ValidationError('Either state or value must be provided')
        return data


class WaterMonitoringDataSerializer(serializers.ModelSerializer):
    """Serializer for Water Monitoring Data."""
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = WaterMonitoringData
        fields = [
            'id', 'device', 'device_name', 'water_percentage', 'tds', 'ph',
            'temperature', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class WaterPumpTimerSerializer(serializers.ModelSerializer):
    """Serializer for Water Pump Timer."""
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = WaterPumpTimer
        fields = [
            'id', 'device', 'device_name', 'hours', 'minutes', 'seconds',
            'is_active', 'is_running', 'created_at', 'updated_at', 'started_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OTAUpdateSerializer(serializers.ModelSerializer):
    """Serializer for OTA Updates."""
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = OTAUpdate
        fields = [
            'id', 'device', 'device_name', 'bin_file', 'file_size', 'checksum',
            'version', 'status', 'download_progress', 'created_at', 'started_at',
            'completed_at', 'notes'
        ]
        read_only_fields = ['id', 'file_size', 'checksum', 'created_at', 'download_progress']

