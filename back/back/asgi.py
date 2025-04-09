# back/asgi.py

import os
import django
from django.core.asgi import get_asgi_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back.settings')

# Initialize Django
django.setup()

# Import the WebSocket application from routing.py
from .routing import application

# Get the ASGI application
django_asgi_app = get_asgi_application()

# Add HTTP support to the application
application.application_mapping['http'] = django_asgi_app
