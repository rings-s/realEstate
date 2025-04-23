# consumers/chat_consumer.py
import json
from channels.db import database_sync_to_async
from django.utils import timezone

from .base_consumer import BaseConsumer

class ChatConsumer(BaseConsumer):
    """Basic chat consumer implementation."""
    group_prefix = 'chat'

    async def get_group_name(self):
        self.room_name = self.params.get('room_name')
        return f'chat_{self.room_name}'

    async def authenticate(self):
        # Basic authentication - allow all for simplicity
        return True

    async def process_message(self, data):
        message_type = data.get('type', 'message')

        if message_type == 'message':
            message_text = data.get('message', '')

            if message_text:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chat_message',
                        'message': message_text,
                        'user_id': str(self.user.id) if self.user.is_authenticated else None,
                        'username': self.user.get_username() if self.user.is_authenticated else 'Anonymous',
                        'timestamp': timezone.now().isoformat()
                    }
                )
        elif message_type == 'typing':
            if self.user.is_authenticated:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': str(self.user.id),
                        'username': self.user.get_username(),
                        'is_typing': data.get('is_typing', False)
                    }
                )

    async def chat_message(self, event):
        """Handle chat message event."""
        await self.send(text_data=json.dumps(event))

    async def typing_indicator(self, event):
        """Handle typing indicator event."""
        await self.send(text_data=json.dumps(event))
