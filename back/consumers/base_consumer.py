# consumers/base_consumer.py

import json
import logging
import traceback
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)

class EnhancedJSONEncoder(DjangoJSONEncoder):
    """
    Enhanced JSON encoder that handles additional types common in our application
    """
    def default(self, obj):
        # Handle UUID objects
        if hasattr(obj, 'hex'):
            return str(obj)
        # Handle datetime objects
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class BaseConsumer(AsyncWebsocketConsumer):
    """
    Enhanced base consumer class with improved error handling, performance monitoring,
    and better serialization support.
    
    Provides authentication, connection management, rate limiting, and error handling.
    """
    # The group name prefix, to be overridden by subclasses
    group_prefix = 'base'
    
    # Maximum message size in bytes
    max_message_size = 262144  # 256 KB
    
    # Rate limiting settings
    rate_limit_messages = 60  # Maximum messages per minute
    rate_limit_window = 60    # Window size in seconds
    
    async def connect(self):
        """
        Handle WebSocket connection with improved error handling
        """
        # Get request ID for logging
        self.request_id = self.scope.get('request_id', 'unknown')
        
        # Extract parameters from URL route
        self.user = self.scope.get('user')
        self.params = self.scope['url_route']['kwargs']
        
        # Initialize rate limiting
        self.message_timestamps = []
        
        try:
            # Authenticate user if required
            if not await self.authenticate():
                logger.warning(f"[{self.request_id}] Authentication failed: {self.group_prefix} connection rejected")
                await self.close(code=4003)  # Authentication failure
                return

            # Set up the group name
            self.group_name = await self.get_group_name()
            if not self.group_name:
                logger.warning(f"[{self.request_id}] Invalid group name, connection rejected")
                await self.close(code=4000)  # Bad request
                return

            # Join the group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            # Accept the connection
            await self.accept()
            logger.info(f"[{self.request_id}] WebSocket connected: {self.group_name}")

            # Send initial data if available
            try:
                initial_data = await self.get_initial_data()
                if initial_data:
                    await self.send(text_data=self.encode_json(initial_data))
            except Exception as e:
                logger.exception(f"[{self.request_id}] Error sending initial data: {str(e)}")
                await self.send_error("Failed to load initial data")
        except Exception as e:
            logger.exception(f"[{self.request_id}] Error during WebSocket connection: {str(e)}")
            await self.close(code=4500)  # Internal server error
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection with proper cleanup
        """
        # Leave the group
        try:
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
                logger.info(f"[{self.request_id}] WebSocket disconnected: {self.group_name}, code: {close_code}")

            # Perform any additional cleanup
            await self.on_disconnect(close_code)
        except Exception as e:
            logger.exception(f"[{self.request_id}] Error during disconnect: {str(e)}")
    
    async def receive(self, text_data):
        """
        Handle messages received from the client with improved validation,
        rate limiting, and error handling
        """
        try:
            # Check message size limit
            if len(text_data) > self.max_message_size:
                await self.send_error(
                    f"Message too large ({len(text_data)} bytes). Maximum size is {self.max_message_size} bytes.",
                    code="message_size_exceeded"
                )
                return

            # Apply rate limiting
            if not await self.check_rate_limit():
                await self.send_error(
                    f"Rate limit exceeded. Maximum {self.rate_limit_messages} messages per {self.rate_limit_window} seconds.",
                    code="rate_limit_exceeded"
                )
                return

            # Parse JSON with proper error handling
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                await self.send_error("Invalid JSON format")
                return

            # Handle ping/pong for keepalive
            if data.get('type') == 'ping':
                await self.send(text_data=self.encode_json({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
                return

            # Process the message
            await self.process_message(data)

        except Exception as e:
            logger.exception(f"[{self.request_id}] Error processing message: {str(e)}")
            
            # Extract client ID for error correlation if available
            client_id = None
            try:
                if text_data:
                    data = json.loads(text_data)
                    client_id = data.get('client_id')
            except:
                pass
                
            # Send error with stack trace in debug mode
            if settings.DEBUG:
                await self.send_error(
                    f"An error occurred: {str(e)}",
                    details=traceback.format_exc() if settings.DEBUG else None,
                    client_id=client_id
                )
            else:
                await self.send_error(
                    "An error occurred processing your request",
                    client_id=client_id
                )
    
    async def send_error(self, message, details=None, code=None, client_id=None):
        """
        Send an enhanced error message to the client
        
        Args:
            message: Main error message
            details: Additional error details (optional)
            code: Error code for client-side handling (optional)
            client_id: Client-provided ID to correlate with request (optional)
        """
        error_data = {
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
        
        if details:
            error_data['details'] = details
        
        if code:
            error_data['code'] = code
        
        if client_id:
            error_data['client_id'] = client_id
        
        # Log the error
        logger.warning(f"[{self.request_id}] Sending WebSocket error: {message} (code: {code})")
        
        # Log details in debug mode
        if settings.DEBUG and details:
            logger.debug(f"[{self.request_id}] Error details: {details}")
        
        await self.send(text_data=self.encode_json(error_data))
    
    async def check_rate_limit(self):
        """
        Check if the client has exceeded rate limits
        
        Returns:
            bool: True if within rate limits, False if exceeded
        """
        current_time = timezone.now().timestamp()
        
        # Remove timestamps outside the current window
        self.message_timestamps = [
            ts for ts in self.message_timestamps 
            if current_time - ts < self.rate_limit_window
        ]
        
        # Check if we've exceeded the rate limit
        if len(self.message_timestamps) >= self.rate_limit_messages:
            logger.warning(f"[{self.request_id}] Rate limit exceeded: {len(self.message_timestamps)} messages in {self.rate_limit_window}s")
            return False
        
        # Add current timestamp to the list
        self.message_timestamps.append(current_time)
        return True
    
    async def get_group_name(self):
        """
        Get the group name for this consumer.
        Override in subclasses if a different naming convention is needed.
        """
        # Default implementation for simple ID-based groups
        if 'id' in self.params:
            return f"{self.group_prefix}_{self.params['id']}"
        elif 'user_id' in self.params:
            return f"{self.group_prefix}_{self.params['user_id']}"
        elif 'auction_id' in self.params:
            return f"{self.group_prefix}_{self.params['auction_id']}"
        elif 'room_name' in self.params:
            return f"{self.group_prefix}_{self.params['room_name']}"
        else:
            # Fallback to a generic name with the first parameter
            param_key = next(iter(self.params), 'general')
            return f"{self.group_prefix}_{self.params.get(param_key, 'general')}"
    
    async def authenticate(self):
        """
        Authenticate the connection.
        Override in subclasses to implement custom authentication.
        """
        # Default implementation - allow all connections
        return True
    
    async def get_initial_data(self):
        """
        Get initial data to send on connection.
        Override in subclasses to provide specific initial data.
        """
        # Default implementation - no initial data
        return None
    
    async def process_message(self, data):
        """
        Process a message received from the client.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process_message")
    
    async def on_disconnect(self, close_code):
        """
        Perform any cleanup needed on disconnect.
        Override in subclasses if needed.
        """
        # Default implementation - no cleanup needed
        pass
    
    def encode_json(self, data):
        """
        Encode data as JSON with improved serialization
        """
        return json.dumps(data, cls=EnhancedJSONEncoder)
    
    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """Get a user by ID"""
        # Import get_user_model inside the method to avoid AppRegistryNotReady errors
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"[{self.request_id}] User {user_id} not found")
            return None
    
    @classmethod
    def encode_datetime(cls, dt):
        """Encode a datetime object for JSON serialization"""
        if dt:
            return dt.isoformat()
        return None
    
    @classmethod
    def format_decimal(cls, value):
        """Format a decimal value for JSON serialization"""
        if value is not None:
            return float(value)
        return None