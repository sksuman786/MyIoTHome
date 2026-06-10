"""
WebSocket URL routing configuration.
"""

from django.urls import re_path
from websocket.consumers import DeviceStatusConsumer, ApplianceControlConsumer

websocket_urlpatterns = [
    re_path(r'ws/devices/$', DeviceStatusConsumer.as_asgi()),
    re_path(r'ws/appliances/$', ApplianceControlConsumer.as_asgi()),
]
