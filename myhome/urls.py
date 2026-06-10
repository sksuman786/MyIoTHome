"""
Main URL configuration for myhome project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Safely ignore duplicate DRF format-suffix converter registrations.
# Some DRF versions call `register_converter` multiple times when multiple
# routers are imported; Django raises ValueError if the same name is
# registered twice. Wrap the register function to no-op for already-registered
# converter names to avoid import-time errors during management commands.
try:
    from django.urls import converters
    _orig_register_converter = converters.register_converter

    def _safe_register_converter(converter, name):
        if name in getattr(converters, 'converters', {}):
            return
        return _orig_register_converter(converter, name)

    converters.register_converter = _safe_register_converter
except Exception:
    # If anything goes wrong here, fallback to normal behavior.
    pass

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/', include('api.urls')),
    
    # Browser-facing account pages
    path('accounts/', include('accounts.web_urls')),
    
    # Dashboard
    path('dashboard/', include('dashboard.urls')),
    
    # Devices
    path('devices/', include('devices.urls')),
    
    # Notifications
    path('notifications/', include('notifications.urls')),
    
    # Home redirect
    path('', lambda r: __import__('django.shortcuts', fromlist=['redirect']).redirect('/dashboard/')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
