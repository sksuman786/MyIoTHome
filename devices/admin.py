from django.contrib import admin
from devices.models import Device, Appliance, ApplianceHistory, DeviceData, DeviceFirmware, WaterMonitoringData


class WaterMonitoringDataInline(admin.TabularInline):
    model = WaterMonitoringData
    fields = ('water_percentage', 'tds', 'ph', 'temperature', 'timestamp')
    readonly_fields = ('water_percentage', 'tds', 'ph', 'temperature', 'timestamp')
    extra = 0
    can_delete = False


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'device_id', 'user', 'device_role', 'status', 'ip_address', 'last_seen')
    list_filter = ('status', 'device_type', 'device_role', 'created_at', 'is_active')
    search_fields = ('device_name', 'device_id', 'mac_address', 'device_role')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_seen')
    fieldsets = (
        ('Device Info', {
            'fields': ('id', 'user', 'device_id', 'device_name', 'device_type', 'device_role', 'status', 'is_active')
        }),
        ('Hardware', {
            'fields': ('firmware_version', 'mac_address', 'ip_address')
        }),
        ('Sensor Data', {
            'fields': ('wifi_signal',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_seen', 'last_heartbeat'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('timezone', 'location', 'description'),
            'classes': ('collapse',)
        }),
    )
    inlines = [WaterMonitoringDataInline]


@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ('name', 'device', 'virtual_pin', 'state', 'room', 'is_active')
    list_filter = ('appliance_type', 'state', 'room', 'is_active')
    search_fields = ('name', 'device__device_name', 'virtual_pin')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_state_change')


@admin.register(ApplianceHistory)
class ApplianceHistoryAdmin(admin.ModelAdmin):
    list_display = ('appliance', 'action', 'new_state', 'triggered_by', 'timestamp')
    list_filter = ('action', 'triggered_by', 'timestamp')
    search_fields = ('appliance__name',)
    readonly_fields = ('id', 'timestamp')


@admin.register(DeviceData)
class DeviceDataAdmin(admin.ModelAdmin):
    list_display = ('device', 'wifi_signal', 'timestamp')
    list_filter = ('device', 'timestamp')
    readonly_fields = ('id', 'timestamp')


@admin.register(WaterMonitoringData)
class WaterMonitoringDataAdmin(admin.ModelAdmin):
    list_display = ('device', 'water_percentage', 'tds', 'ph', 'temperature', 'timestamp')
    list_filter = ('device', 'timestamp')
    readonly_fields = ('id', 'device', 'water_percentage', 'tds', 'ph', 'temperature', 'timestamp')
    search_fields = ('device__device_id', 'device__device_name')


@admin.register(DeviceFirmware)
class DeviceFirmwareAdmin(admin.ModelAdmin):
    list_display = ('version', 'device_type', 'status', 'released_at', 'created_at')
    list_filter = ('device_type', 'status', 'created_at')
    search_fields = ('version', 'changelog')
    readonly_fields = ('id', 'created_at')
