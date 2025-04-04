# consumers/middleware.py
import logging
import time
import uuid
from urllib.parse import parse_qs
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.conf import settings
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidTokenError

User = get_user_model()
logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user(user_id):
    """
    Get user by ID with proper error handling
    
    Args:
        user_id: User ID
        
    Returns:
        User object if found, AnonymousUser otherwise
    """
    try:
        # Close old database connections to prevent issues
        close_old_connections()
        
        # Try to get the user
        user = User.objects.get(id=user_id)
        
        # Ensure user is active
        if not user.is_active:
            logger.warning(f"Inactive user {user_id} attempted WebSocket connection")
            return AnonymousUser()
            
        return user
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found for WebSocket connection")
        return AnonymousUser()
    except Exception as e:
        logger.exception(f"Error retrieving user {user_id}: {str(e)}")
        return AnonymousUser()

@database_sync_to_async
def get_user_from_token(token_key):
    """
    Get user from JWT token with improved error handling
    
    Args:
        token_key: JWT token string
        
    Returns:
        User object if valid token, AnonymousUser otherwise
    """
    try:
        # Close old database connections
        close_old_connections()
        
        # Use the SimpleJWT AccessToken class if available
        try:
            from rest_framework_simplejwt.tokens import AccessToken, TokenError
            
            # Parse the token
            token = AccessToken(token_key)
            
            # Get user from token payload
            user_id = token.payload.get('user_id')
            if not user_id:
                logger.warning("JWT token missing user_id claim")
                return AnonymousUser()
                
            # Get user from database
            user = User.objects.get(id=user_id)
            
            # Ensure user is active
            if not user.is_active:
                logger.warning(f"Inactive user {user_id} attempted WebSocket connection")
                return AnonymousUser()
                
            return user
        except (TokenError, InvalidTokenError) as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return AnonymousUser()
            
    except Exception as e:
        logger.exception(f"JWT authentication error: {str(e)}")
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    """
    Enhanced JWT authentication middleware for Channels with better error handling
    and performance optimizations
    """
    
    async def __call__(self, scope, receive, send):
        # Add unique request ID for tracking
        request_id = str(uuid.uuid4())
        scope['request_id'] = request_id
        
        # Start timing for metrics
        start_time = time.time()
        
        # Close old database connections to prevent connection pooling issues
        close_old_connections()
        
        # Get the user and track metrics
        try:
            user = await self.get_user_from_scope(scope)
            scope['user'] = user
            
            # Add connection start time for metrics
            scope['_metrics'] = {
                'connect_time': start_time,
                'request_id': request_id
            }
            
            # Log authentication result
            if user.is_authenticated:
                logger.info(f"[{request_id}] WebSocket authenticated as {user.id}")
            else:
                logger.info(f"[{request_id}] WebSocket anonymous connection")
                
            # Call the next middleware or the consumer
            return await super().__call__(scope, receive, send)
        except Exception as e:
            logger.exception(f"[{request_id}] Error during WebSocket authentication: {str(e)}")
            scope['user'] = AnonymousUser()
            return await super().__call__(scope, receive, send)
        finally:
            # Log total auth time for performance monitoring
            auth_time = time.time() - start_time
            if auth_time > 0.5:  # Only log slow authentications
                logger.warning(f"[{request_id}] Slow WebSocket authentication: {auth_time:.2f}s")
    
    async def get_user_from_scope(self, scope):
        """
        Extract and validate user from the WebSocket scope
        with enhanced token handling
        
        Args:
            scope: WebSocket connection scope
            
        Returns:
            User object if authenticated, AnonymousUser otherwise
        """
        request_id = scope.get('request_id', 'unknown')
        
        # Check if scope already has a user (e.g., from session)
        if 'user' in scope and scope['user'] is not None and scope['user'].is_authenticated:
            return scope['user']
            
        # Try different token sources in order of preference
        token = None
        
        # 1. Check query string for token (most common for WebSockets)
        query_string = scope.get('query_string', b'').decode()
        if query_string:
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            
        # 2. Check headers for token if not found in query string
        if not token and 'headers' in scope:
            headers = dict(scope['headers'])
            auth_header = headers.get(b'authorization', b'').decode().split()
            if len(auth_header) == 2 and auth_header[0].lower() == 'bearer':
                token = auth_header[1]
                
        # If no token, use an anonymous user
        if not token:
            logger.debug(f"[{request_id}] No authentication token provided")
            return AnonymousUser()
            
        # First, try to use rest_framework_simplejwt if available
        try:
            return await get_user_from_token(token)
        except ImportError:
            # Fall back to manual JWT validation if simplejwt is not available
            pass
            
        # Manual JWT validation
        try:
            # Get the algorithm and secret key from settings
            algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
            secret_key = getattr(settings, 'SECRET_KEY', '')
            
            # Decode the token
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            
            # Get the user ID from the payload
            user_id = payload.get('user_id')
            if not user_id:
                logger.warning(f"[{request_id}] JWT token missing user_id claim")
                return AnonymousUser()
                
            # Get the user from the database
            return await get_user(user_id)
        except ExpiredSignatureError:
            logger.warning(f"[{request_id}] JWT token expired")
            return AnonymousUser()
        except PyJWTError as e:
            logger.warning(f"[{request_id}] JWT authentication error: {str(e)}")
            return AnonymousUser()
        except Exception as e:
            logger.exception(f"[{request_id}] Error during WebSocket authentication: {str(e)}")
            return AnonymousUser()

class MetricsMiddleware(BaseMiddleware):
    """
    Middleware to collect and report metrics for WebSocket connections
    """
    
    async def __call__(self, scope, receive, send):
        # Start time tracking
        start_time = time.time()
        request_id = scope.get('request_id', str(uuid.uuid4()))
        
        # Extract data from scope
        connection_type = scope['type']
        path = scope.get('path', 'unknown')
        client_host = scope.get('client', ['unknown', 0])[0]
        
        # Skip non-websocket requests
        if connection_type != 'websocket':
            return await super().__call__(scope, receive, send)
            
        # Initialize connection metrics
        if '_metrics' not in scope:
            scope['_metrics'] = {}
            
        scope['_metrics'].update({
            'request_id': request_id,
            'connect_time': start_time,
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'path': path,
            'client_host': client_host,
        })
        
        # Create wrapped receive and send functions to track messages
        async def metrics_receive():
            message = await receive()
            if message['type'] == 'websocket.receive':
                scope['_metrics']['messages_received'] += 1
                
                # Log message statistics for debugging
                if settings.DEBUG and message.get('text', '').startswith('{'):
                    logger.debug(f"[{request_id}] Received WebSocket message: {message.get('text', '')[:200]}...")
                    
            return message
            
        async def metrics_send(message):
            if message['type'] == 'websocket.send':
                scope['_metrics']['messages_sent'] += 1
                
                # Log message statistics for debugging
                if settings.DEBUG and message.get('text', '').startswith('{'):
                    logger.debug(f"[{request_id}] Sent WebSocket message: {message.get('text', '')[:200]}...")
                    
            elif message['type'] == 'websocket.close':
                # Log connection metrics when closing
                duration = time.time() - scope['_metrics']['connect_time']
                messages_received = scope['_metrics']['messages_received']
                messages_sent = scope['_metrics']['messages_sent']
                errors = scope['_metrics']['errors']
                
                logger.info(
                    f"[{request_id}] WebSocket metrics - Path: {path}, "
                    f"Duration: {duration:.2f}s, Messages received: {messages_received}, "
                    f"Messages sent: {messages_sent}, Errors: {errors}"
                )
                
                # Store metrics in database or send to monitoring system
                try:
                    await self.store_metrics(scope['_metrics'], duration)
                except Exception as e:
                    logger.error(f"[{request_id}] Error storing WebSocket metrics: {str(e)}")
                
            await send(message)
        
        try:
            # Call the next middleware or consumer with our wrapped functions
            return await super().__call__(scope, metrics_receive, metrics_send)
        except Exception as e:
            # Track errors
            if '_metrics' in scope:
                scope['_metrics']['errors'] += 1
            
            # Log the error
            logger.exception(f"[{request_id}] WebSocket error: {str(e)}")
            
            # Re-raise the exception
            raise
    
    async def store_metrics(self, metrics, duration):
        """
        Store WebSocket metrics - can be implemented to store in database
        or send to a monitoring system.
        
        This is a placeholder implementation.
        """
        # In a real implementation, you might store these metrics in your database
        # or send them to a monitoring system like Prometheus, Datadog, etc.
        pass