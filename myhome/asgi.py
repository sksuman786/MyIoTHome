"""
ASGI config for myhome project.
This file provides a simple ASGI application that delegates to Django's
`get_asgi_application`. Channels and WebSocket routing have been removed
for a cPanel / single-process deployment.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhome.settings')

application = get_asgi_application()
