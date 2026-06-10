#!/usr/bin/env python
"""
Passenger WSGI entrypoint for cPanel deployments.

Place this file in the project root (next to `manage.py`). Configure the
Python App in cPanel to use this as the application startup file.
"""
import os
import sys

# Project base directory (assumes this file is in project root)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# Optionally add the project package directory
sys.path.insert(0, os.path.join(PROJECT_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhome.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
