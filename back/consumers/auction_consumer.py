import json
from channels.db import database_sync_to_async
from django.utils import timezone

from .base_consumer import BaseConsumer
from base.models import Auction

class AuctionConsumer(BaseConsumer):
    """WebSocket consumer for real-time auction updates."""
    group_prefix = 'auction'

    async def get_group_name(self):
        self.auction_id = self.params.get('auction_id')
        return f'auction_{self.auction_id}'

    async def authenticate(self):
        auction = await self.get_auction()
        if not auction:
            return False
        self.auction = auction
        return True

    async def get_initial_data(self):
        try:
            return {
                'type': 'initial_state',
                'auction_id': str(self.auction.id),
                'title': self.auction.title,
                'status': self.auction.status,
                'current_bid': self.format_decimal(self.auction.current_bid),
                'starting_bid': self.format_decimal(self.auction.starting_bid),
                'min_bid_increment': self.format_decimal(self.auction.minimum_increment),
                'bid_count': self.auction.bid_count,
                'start_date': self.encode_datetime(self.auction.start_date),
                'end_date': self.encode_datetime(self.auction.end_date),
                'time_remaining': self.auction.time_remaining,
                'property': {
                    'id': str(self.auction.related_property.id),
                    'title': self.auction.related_property.title,
                } if self.auction.related_property else None
            }
        except Exception as e:
            logger.error(f"Error getting initial auction data: {str(e)}")
            return {'type': 'error', 'message': 'Failed to load auction data'}

    async def process_message(self, data):
        action = data.get('action')

        if action == 'get_state':
            auction = await self.get_auction(refresh=True)
            if auction:
                self.auction = auction
                await self.send(text_data=json.dumps({
                    'type': 'auction_state',
                    'auction_id': str(auction.id),
                    'status': auction.status,
                    'current_bid': self.format_decimal(auction.current_bid),
                    'bid_count': auction.bid_count,
                    'time_remaining': auction.time_remaining,
                    'end_date': self.encode_datetime(auction.end_date)
                }))
            else:
                await self.send_error('Auction not found')
        elif action in ['watch_auction', 'unwatch_auction', 'get_watch_status']:
            if not self.user.is_authenticated:
                await self.send_error('Authentication required')
                return

            if action == 'watch_auction':
                success = await self.register_auction_watch()
                await self.send(text_data=json.dumps({'type': 'watch_status', 'is_watching': success}))
            elif action == 'unwatch_auction':
                success = await self.unregister_auction_watch()
                await self.send(text_data=json.dumps({'type': 'watch_status', 'is_watching': not success}))
            elif action == 'get_watch_status':
                is_watching = await self.is_watching_auction()
                await self.send(text_data=json.dumps({'type': 'watch_status', 'is_watching': is_watching}))

    # Event handlers
    async def auction_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': event['status'],
            'status_display': event['status_display'],
            'message': event.get('message'),
            'timestamp': event.get('timestamp', self.encode_datetime(timezone.now()))
        }))

    async def time_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'time_update',
            'time_remaining': event['time_remaining'],
            'end_date': event['end_date'],
            'is_extended': event.get('is_extended', False),
            'timestamp': event.get('timestamp', self.encode_datetime(timezone.now()))
        }))

    # Database methods
    @database_sync_to_async
    def get_auction(self, refresh=False):
        try:
            if refresh or not hasattr(self, 'auction'):
                return Auction.objects.get(id=self.auction_id)
            return self.auction
        except Auction.DoesNotExist:
            return None

    @database_sync_to_async
    def register_auction_watch(self):
        try:
            auction = Auction.objects.get(id=self.auction_id)
            if hasattr(auction, 'watched_by'):
                auction.watched_by.add(self.user)
            else:
                if not hasattr(auction, 'metadata') or not isinstance(auction.metadata, dict):
                    auction.metadata = {}
                watchers = auction.metadata.get('watchers', [])
                if str(self.user.id) not in watchers:
                    watchers.append(str(self.user.id))
                    auction.metadata['watchers'] = watchers
                    auction.save(update_fields=['metadata'])
            return True
        except Exception:
            return False

    @database_sync_to_async
    def unregister_auction_watch(self):
        try:
            auction = Auction.objects.get(id=self.auction_id)
            if hasattr(auction, 'watched_by'):
                auction.watched_by.remove(self.user)
            else:
                if not hasattr(auction, 'metadata') or not isinstance(auction.metadata, dict):
                    return False
                watchers = auction.metadata.get('watchers', [])
                if str(self.user.id) in watchers:
                    watchers.remove(str(self.user.id))
                    auction.metadata['watchers'] = watchers
                    auction.save(update_fields=['metadata'])
            return True
        except Exception:
            return False

    @database_sync_to_async
    def is_watching_auction(self):
        try:
            auction = Auction.objects.get(id=self.auction_id)
            if hasattr(auction, 'watched_by'):
                return auction.watched_by.filter(id=self.user.id).exists()
            else:
                if not hasattr(auction, 'metadata') or not isinstance(auction.metadata, dict):
                    return False
                watchers = auction.metadata.get('watchers', [])
                return str(self.user.id) in watchers
            return False
        except Exception:
            return False
