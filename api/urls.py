"""
URL configuration for API app.
"""

from django.urls import path
from api.views import (
    device_auth, get_appliance_states, update_device_status, device_heartbeat,
    update_appliance_state, confirm_appliance_state, set_appliance_state, api_documentation,
    save_water_monitoring_data, get_water_monitoring_data, create_pump_timer,
    get_pump_timer, start_pump_timer, get_device_pump_timer, upload_ota_update,
    get_ota_update_download, update_ota_progress, ota_check_version, system_status
)

urlpatterns = [
    # Device Authentication
    path('device/auth/', device_auth, name='device-auth'),
    
    # Appliance States
    path('device/states/', get_appliance_states, name='device-states'),
    
    # Device Status
    path('device/status/', update_device_status, name='device-status'),
    
    # Heartbeat
    path('device/heartbeat/', device_heartbeat, name='device-heartbeat'),

    # System status for external monitoring apps
    path('system/status/', system_status, name='system-status'),
    
    # Appliance State Management
    path('device/appliance/state/', update_appliance_state, name='appliance-state'),
    path('device/appliance/confirm/', confirm_appliance_state, name='appliance-confirm'),
    path('device/appliance/set/', set_appliance_state, name='appliance-set'),
    
    # Water Monitoring
    path('device/water/data/', save_water_monitoring_data, name='save-water-data'),
    path('device/water/data/get/', get_water_monitoring_data, name='get-water-data'),
    
    # Water Pump Timer
    path('water/pump/timer/', create_pump_timer, name='create-pump-timer'),
    path('water/pump/timer/get/', get_pump_timer, name='get-pump-timer'),
    path('device/water/pump/start/', start_pump_timer, name='start-pump-timer'),
    path('device/water/pump/timer/status/', get_device_pump_timer, name='device-pump-timer-status'),
    
    # OTA Updates
    path('ota/check/', ota_check_version, name='check-ota'),
    path('ota/upload/', upload_ota_update, name='upload-ota'),
    path('device/ota/download/', get_ota_update_download, name='download-ota'),
    path('device/ota/progress/', update_ota_progress, name='update-ota-progress'),
    
    # Documentation
    path('docs/', api_documentation, name='api-docs'),
]
