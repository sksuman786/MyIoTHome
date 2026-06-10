from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import now
import uuid
import secrets
import string

User = get_user_model()


class Device(models.Model):
    """
    IoT Device model for ESP8266/ESP32 devices.
    Each device belongs to a user and contains multiple appliances.
    """
    DEVICE_TYPE_CHOICES = (
        ('esp8266', 'ESP8266'),
        ('esp32', 'ESP32'),
        ('other', 'Other'),
    )
    DEVICE_ROLE_CHOICES = (
        ('standard', 'Standard'),
        ('water_monitor', 'Water Monitor'),
    )
    
    STATUS_CHOICES = (
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('inactive', 'Inactive'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=100, unique=True, db_index=True)
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, default='esp8266')
    device_role = models.CharField(max_length=20, choices=DEVICE_ROLE_CHOICES, default='standard', help_text='Designates the device role, such as a dedicated water monitoring device.')
    
    # API Key for device authentication
    
    # Device information
    firmware_version = models.CharField(max_length=20, default='1.0.0')
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    is_active = models.BooleanField(default=True)
    
    # Environmental data
    wifi_signal = models.IntegerField(null=True, blank=True, help_text="WiFi signal strength (dBm)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    # Heartbeat timeout in seconds — device considered offline after this
    # Use a class attribute (non-db) default so migrations are optional.
    heartbeat_timeout_seconds = 50
    
    # Configuration
    timezone = models.CharField(max_length=50, default='UTC')
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-last_seen']
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        indexes = [
            models.Index(fields=['user', '-last_seen']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.device_name} ({self.device_id})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
    
    def is_online(self):
        """Check if device is online based on last heartbeat."""
        from django.utils.timezone import now
        from datetime import timedelta
        if not self.last_heartbeat:
            return False
        return (now() - self.last_heartbeat) < timedelta(seconds=self.heartbeat_timeout_seconds)


class Appliance(models.Model):
    """
    Appliance/Switch model for controlling devices.
    Each appliance is connected to a pin on the device.
    """
    APPLIANCE_TYPE_CHOICES = (
        ('light', 'Light'),
        ('fan', 'Fan'),
        ('switch', 'Switch'),
        ('door', 'Door/Gate'),
        ('pump', 'Pump'),
        ('slider', 'Slider'),
        ('display', 'Display'),
        ('other', 'Other'),
    )
    
    STATE_CHOICES = (
        (0, 'OFF'),
        (1, 'ON'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='appliances')
    
    # Appliance details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    appliance_type = models.CharField(max_length=20, choices=APPLIANCE_TYPE_CHOICES, default='switch')
    
    # Pin and state
    pin = models.CharField(max_length=10, help_text="V0, V1, V2, etc. or GPIO pin number")
    virtual_pin = models.CharField(max_length=10, db_index=True, help_text="Virtual pin like V0, V1")

    # Current state
    state = models.IntegerField(choices=STATE_CHOICES, default=0)
    value = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Numeric slider/display value, e.g. 1-7 for slider or display output"
    )
    icon = models.CharField(max_length=50, default='fa-power-off')  # Font Awesome icon
    
    # Room/Location
    room = models.CharField(max_length=100, blank=True, null=True)
    
    # Power consumption
    power_consumption = models.FloatField(null=True, blank=True, help_text="Power consumption in watts")
    
    # Control settings
    can_control = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_state_change = models.DateTimeField(null=True, blank=True)
    
    # History
    total_on_time = models.BigIntegerField(default=0, help_text="Total ON time in seconds")
    
    class Meta:
        ordering = ['room', 'name']
        verbose_name = 'Appliance'
        verbose_name_plural = 'Appliances'
        unique_together = ('device', 'virtual_pin')
        indexes = [
            models.Index(fields=['device', 'virtual_pin']),
            models.Index(fields=['state']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.device.device_name} - {self.virtual_pin})"
    
    def toggle(self):
        """Toggle appliance state."""
        self.state = 1 if self.state == 0 else 0
        self.save()
        return self.state


class ApplianceHistory(models.Model):
    """
    History of appliance state changes and control actions.
    """
    ACTION_CHOICES = (
        ('turned_on', 'Turned ON'),
        ('turned_off', 'Turned OFF'),
        ('toggled', 'Toggled'),
        ('auto_on', 'Auto ON'),
        ('auto_off', 'Auto OFF'),
        ('timer_on', 'Timer ON'),
        ('timer_off', 'Timer OFF'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE, related_name='history')
    
    # State information
    previous_state = models.IntegerField(choices=Appliance.STATE_CHOICES)
    new_state = models.IntegerField(choices=Appliance.STATE_CHOICES)
    
    # Action and source
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='turned_on')
    triggered_by = models.CharField(max_length=50, choices=[('user', 'User'), ('automation', 'Automation'), ('timer', 'Timer'), ('device', 'Device')])
    
    # User who triggered the action (if applicable)
    triggered_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Duration (if turned off)
    duration = models.DurationField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Appliance History'
        verbose_name_plural = 'Appliance History'
        indexes = [
            models.Index(fields=['appliance', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.appliance.name}: {self.get_action_display()} at {self.timestamp}"


class DeviceData(models.Model):
    """
    Store sensor and environmental data from devices.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='data_logs')
    
    # Environmental data
    # Removed temperature/humidity/pressure fields per request; keep only network and metrics
    
    # Network data
    wifi_signal = models.IntegerField(null=True, blank=True)
    wifi_quality = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Device metrics
    uptime = models.BigIntegerField(null=True, blank=True, help_text="Uptime in seconds")
    free_memory = models.BigIntegerField(null=True, blank=True, help_text="Free memory in bytes")
    power_consumption = models.FloatField(null=True, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Device Data'
        verbose_name_plural = 'Device Data'
        indexes = [
            models.Index(fields=['device', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.device_name} - {self.timestamp}"


class DeviceFirmware(models.Model):
    """
    Manage firmware versions for devices.
    """
    FIRMWARE_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('testing', 'Testing'),
        ('stable', 'Stable'),
        ('deprecated', 'Deprecated'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=20, unique=True)
    device_type = models.CharField(max_length=20, choices=Device.DEVICE_TYPE_CHOICES)
    
    # File information
    file = models.FileField(upload_to='firmware/')
    file_size = models.BigIntegerField(help_text="File size in bytes")
    checksum = models.CharField(max_length=64, unique=True)
    
    # Description
    changelog = models.TextField()
    release_notes = models.TextField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=FIRMWARE_STATUS_CHOICES, default='draft')
    
    # Timeline
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    deprecated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Device Firmware'
        verbose_name_plural = 'Device Firmware'
    
    def __str__(self):
        return f"{self.device_type} v{self.version} ({self.get_status_display()})"


class WaterMonitoringData(models.Model):
    """
    Store water quality monitoring data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='water_data')
    
    # Water quality metrics
    water_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Water level percentage (0-100)")
    tds = models.FloatField(help_text="Total Dissolved Solids in ppm")
    ph = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(14)], help_text="pH value (0-14)")
    temperature = models.FloatField(help_text="Water temperature in Celsius")
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Water Monitoring Data'
        verbose_name_plural = 'Water Monitoring Data'
        indexes = [
            models.Index(fields=['device', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.device_name} - Water Data ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class WaterPumpTimer(models.Model):
    """
    Store water pump timer settings for automation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='pump_timers')
    
    # Timer settings
    hours = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(23)])
    minutes = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(59)])
    seconds = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(59)])
    
    # Status
    is_active = models.BooleanField(default=False)
    is_running = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True, help_text="When the timer was last started")

    @property
    def total_seconds(self):
        return self.hours * 3600 + self.minutes * 60 + self.seconds

    @property
    def remaining_seconds(self):
        if not self.is_running or not self.started_at:
            return 0
        elapsed = (now() - self.started_at).total_seconds()
        remaining = self.total_seconds - int(elapsed)
        return max(0, remaining)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Water Pump Timer'
        verbose_name_plural = 'Water Pump Timers'
    
    def __str__(self):
        return f"{self.device.device_name} - Timer ({self.hours}h:{self.minutes}m:{self.seconds}s)"


class OTAUpdate(models.Model):
    """
    Manage OTA (Over-The-Air) firmware updates for devices.
    """
    OTA_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('downloading', 'Downloading'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='ota_updates')
    
    # File information
    bin_file = models.FileField(upload_to='ota_updates/', help_text="Binary firmware file (.bin)")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    checksum = models.CharField(max_length=64, help_text="SHA256 checksum of file")
    
    # Version information
    version = models.CharField(max_length=20, help_text="Firmware version e.g. v1.2.3")
    
    # Status
    status = models.CharField(max_length=20, choices=OTA_STATUS_CHOICES, default='pending')
    
    # Progress tracking
    download_progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'OTA Update'
        verbose_name_plural = 'OTA Updates'
    
    def __str__(self):
        return f"{self.device.device_name} - OTA v{self.version} ({self.get_status_display()})"
