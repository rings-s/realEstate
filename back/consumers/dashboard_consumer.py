# consumers/dashboard_consumer.py
import json
from channels.db import database_sync_to_async
from django.utils import timezone

from .base_consumer import BaseConsumer

class DashboardConsumer(BaseConsumer):
    """Basic dashboard consumer implementation."""
    group_prefix = 'dashboard'

    async def get_group_name(self):
        self.user_id = self.params.get('user_id')
        return f'dashboard_{self.user_id}'

    async def authenticate(self):
        # Only authenticated users who match the requested user_id
        if not self.user.is_authenticated:
            return False

        # Allow staff to access any dashboard
        if self.user.is_staff:
            return True

        # Regular users can only access their own dashboard
        return str(self.user.id) == self.params.get('user_id')

    async def process_message(self, data):
        action = data.get('action', '')

        if action == 'refresh_dashboard':
            await self.send(text_data=json.dumps({
                'type': 'dashboard_data',
                'data': {
                    'status': 'success',
                    'message': 'Dashboard refreshed',
                    'timestamp': timezone.now().isoformat()
                }
            }))

    async def notification_event(self, event):
        """Handle notification events."""
        await self.send(text_data=json.dumps(event))

    async def dashboard_update(self, event):
        """Handle dashboard updates."""
        await self.send(text_data=json.dumps(event))
