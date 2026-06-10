"""
URL configuration for dashboard app.
"""

from django.urls import path
from dashboard.views import (
    dashboard_view, devices_view, device_detail_view, rooms_view,
    activity_logs_view, notifications_view, profile_view, settings_view,
    dashboard_stats, dashboard_data, water_monitoring_view, ota_update_view,
    ota_updates_api, ota_download_api, toggle_pump_api, pump_status_api, start_timer_api, stop_timer_api
)

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('devices/', devices_view, name='devices'),
    path('devices/<uuid:device_id>/', device_detail_view, name='device-detail'),
    path('rooms/', rooms_view, name='rooms'),
    path('activity/', activity_logs_view, name='activity-logs'),
    path('notifications/', notifications_view, name='notifications'),
    path('profile/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),
    path('water-monitoring/', water_monitoring_view, name='water-monitoring'),
    path('ota-update/', ota_update_view, name='ota-update'),
    
    # Dashboard API endpoints
    path('api/water/pump/toggle/', toggle_pump_api, name='dashboard-toggle-pump'),
    path('api/water/pump/status/', pump_status_api, name='dashboard-pump-status'),
    path('api/water/pump/start/', start_timer_api, name='dashboard-start-timer'),
    path('api/water/pump/stop/', stop_timer_api, name='dashboard-stop-timer'),

    # API endpoints
    path('api/stats/', dashboard_stats, name='dashboard-stats'),
    path('api/data/', dashboard_data, name='dashboard-data'),
    path('api/ota/updates/', ota_updates_api, name='ota-updates-api'),
    path('api/ota/download/<uuid:update_id>/', ota_download_api, name='ota-download-api'),
]
