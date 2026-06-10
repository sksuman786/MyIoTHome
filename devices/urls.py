"""
URL configuration for devices app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from devices.views import DeviceViewSet, ApplianceViewSet, DeviceFirmwareViewSet

router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'appliances', ApplianceViewSet, basename='appliance')
router.register(r'firmware', DeviceFirmwareViewSet, basename='firmware')

urlpatterns = [
    path('', include(router.urls)),
]
