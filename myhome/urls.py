"""
Main URL configuration for myhome project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

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
