# asgi.py
import os
import django
import logging

# Set ASGI environment flag before Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back.settings')
os.environ['RUNNING_ASGI'] = 'True'  # Add this flag

# Initialize Django
django.setup()

# Import after Django setup
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Import custom middleware
from consumers.middleware import JwtAuthMiddleware
from .routing import websocket_urlpatterns

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Initializing ASGI application with WebSocket support")

# Get Django's ASGI application
django_asgi_app = get_asgi_application()

# Create ASGI application with JWT authentication for WebSockets
application = ProtocolTypeRouter({
    # Django's ASGI application for HTTP
    "http": django_asgi_app,

    # WebSocket handler with JWT auth
    "websocket": AllowedHostsOriginValidator(
        JwtAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

# Log available routes in debug mode
if os.environ.get('DEBUG', 'False') == 'True':
    logger.debug("Available WebSocket routes:")
    for route in websocket_urlpatterns:
        logger.debug(f"  {route.pattern}")