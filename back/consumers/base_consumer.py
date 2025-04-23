import json
import logging
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)

class BaseConsumer(AsyncWebsocketConsumer):
    """Base WebSocket consumer with authentication and error handling."""
    group_prefix = 'base'

    async def connect(self):
        self.user = self.scope.get('user')
        self.params = self.scope['url_route']['kwargs']

        if not await self.authenticate():
            await self.close(code=4003)
            return

        self.group_name = await self.get_group_name()
        if not self.group_name:
            await self.close(code=4000)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        initial_data = await self.get_initial_data()
        if initial_data:
            await self.send(text_data=json.dumps(initial_data, cls=DjangoJSONEncoder))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            # Handle ping/pong for keepalive
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
                return

            await self.process_message(data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.exception(f"Error processing message: {str(e)}")
            await self.send_error("An error occurred processing your request")

    async def send_error(self, message, code=None, client_id=None):
        """Send error message to client."""
        error_data = {
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }

        if code:
            error_data['code'] = code

        if client_id:
            error_data['client_id'] = client_id

        await self.send(text_data=json.dumps(error_data, cls=DjangoJSONEncoder))

    async def get_group_name(self):
        """Get group name for this consumer. Override in subclasses."""
        if 'id' in self.params:
            return f"{self.group_prefix}_{self.params['id']}"
        elif 'auction_id' in self.params:
            return f"{self.group_prefix}_{self.params['auction_id']}"
        elif 'user_id' in self.params:
            return f"{self.group_prefix}_{self.params['user_id']}"
        elif 'room_name' in self.params:
            return f"{self.group_prefix}_{self.params['room_name']}"
        return f"{self.group_prefix}_general"

    async def authenticate(self):
        """Authenticate the connection. Override in subclasses."""
        return True

    async def get_initial_data(self):
        """Get initial data to send on connection. Override in subclasses."""
        return None

    async def process_message(self, data):
        """Process a message from the client. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement process_message")

    @staticmethod
    def encode_datetime(dt):
        """Encode datetime for JSON serialization."""
        return dt.isoformat() if dt else None

    @staticmethod
    def format_decimal(value):
        """Format decimal for JSON serialization."""
        return float(value) if value is not None else None
