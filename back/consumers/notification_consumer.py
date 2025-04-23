# consumers/notification_consumer.py
import json
from channels.db import database_sync_to_async
from django.utils import timezone

from .base_consumer import BaseConsumer

class NotificationConsumer(BaseConsumer):
    """Basic notification consumer implementation."""
    group_prefix = 'notifications'

    async def get_group_name(self):
        self.user_id = self.params.get('user_id')
        return f'notifications_{self.user_id}'

    async def authenticate(self):
        # Only authenticated users who match the requested user_id
        if not self.user.is_authenticated:
            return False

        # Regular users can only access their own notifications
        return str(self.user.id) == self.params.get('user_id')

    async def process_message(self, data):
        action = data.get('action', '')

        if action == 'mark_read':
            notification_id = data.get('notification_id')
            if notification_id:
                await self.send(text_data=json.dumps({
                    'type': 'notification_read',
                    'notification_id': notification_id,
                    'success': True
                }))
        elif action == 'mark_all_read':
            await self.send(text_data=json.dumps({
                'type': 'all_read',
                'success': True
            }))

    async def notification_message(self, event):
        """Handle new notification event."""
        await self.send(text_data=json.dumps(event))
