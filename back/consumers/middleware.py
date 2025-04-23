import logging
from urllib.parse import parse_qs
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.conf import settings
import jwt
from jwt.exceptions import PyJWTError
import time

logger = logging.getLogger(__name__)
User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    """Get user by ID with proper error handling."""
    try:
        close_old_connections()
        user = User.objects.get(id=user_id)
        return user if user.is_active else AnonymousUser()
    except Exception:
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    """JWT authentication middleware for Channels."""

    async def __call__(self, scope, receive, send):
        # Close old database connections
        close_old_connections()

        # Get the user
        scope['user'] = await self._get_user_from_scope(scope)
        return await super().__call__(scope, receive, send)

    async def _get_user_from_scope(self, scope):
        # Try different token sources
        token = None

        # Check query string for token
        query_string = scope.get('query_string', b'').decode()
        if query_string:
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

        # Check headers for token
        if not token and 'headers' in scope:
            headers = dict(scope['headers'])
            auth_header = headers.get(b'authorization', b'').decode().split()
            if len(auth_header) == 2 and auth_header[0].lower() == 'bearer':
                token = auth_header[1]

        if not token:
            return AnonymousUser()

        try:
            # Decode the token
            algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
            secret_key = getattr(settings, 'SECRET_KEY', '')
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])

            # Get the user ID
            user_id = payload.get('user_id')
            if not user_id:
                return AnonymousUser()

            # Get the user
            return await get_user(user_id)
        except PyJWTError:
            return AnonymousUser()



class MetricsMiddleware(BaseMiddleware):
    """Simplified metrics middleware for WebSockets."""

    async def __call__(self, scope, receive, send):
        # Add metrics data to scope
        start_time = time.time()
        scope['_metrics'] = {
            'start_time': start_time,
            'path': scope.get('path', 'unknown')
        }

        # Create wrapped receive and send functions
        async def metrics_receive():
            message = await receive()
            if message.get('type') == 'websocket.receive':
                scope['_metrics']['last_message'] = time.time()
            return message

        async def metrics_send(message):
            if message.get('type') == 'websocket.close':
                # Calculate duration
                duration = time.time() - start_time
                scope['_metrics']['duration'] = duration
            await send(message)

        # Call the next middleware or consumer
        return await super().__call__(scope, metrics_receive, metrics_send)
