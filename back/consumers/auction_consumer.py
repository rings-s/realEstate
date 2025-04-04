# consumers/auction_consumer.py

import json
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model

from .base_consumer import BaseConsumer
from base.models import Auction, Bid
import logging  # Add this line


User = get_user_model()
logger = logging.getLogger(__name__)

class AuctionConsumer(BaseConsumer):
    """
    WebSocket consumer for real-time auction updates.
    Provides status changes, price updates, and time remaining updates.
    """
    group_prefix = 'auction'

    async def get_group_name(self):
        """Get the group name based on the auction ID"""
        self.auction_id = self.params.get('auction_id')
        return f'auction_{self.auction_id}'

    async def authenticate(self):
        """Basic authentication - verify auction exists"""
        auction = await self.get_auction()
        if not auction:
            return False

        # Store auction for later use
        self.auction = auction
        return True

    async def get_initial_data(self):
        """Get initial auction data to send on connect"""
        try:
            # Get auction information
            auction_data = {
                'type': 'initial_state',
                'auction_id': str(self.auction.id),
                'uuid': str(self.auction.uuid),
                'title': self.auction.title,
                'status': self.auction.status,
                'status_display': self.auction.get_status_display(),
                'current_bid': self.format_decimal(self.auction.current_bid),
                'starting_price': self.format_decimal(self.auction.starting_price),
                'min_bid_increment': self.format_decimal(self.auction.min_bid_increment),
                'reserve_price': self.format_decimal(self.auction.reserve_price),
                'bid_count': self.auction.bid_count,
                'unique_bidders_count': self.auction.unique_bidders_count,
                'start_date': self.encode_datetime(self.auction.start_date),
                'end_date': self.encode_datetime(self.auction.end_date),
                'time_remaining': self.auction.time_remaining,
                'is_active': self.auction.is_active,
                'is_extended': self.auction.status == 'extended',
                'property': {
                    'id': str(self.auction.related_property.id),
                    'title': self.auction.related_property.title,
                    'property_type': self.auction.related_property.property_type,
                    'property_type_display': self.auction.related_property.get_property_type_display(),
                    'city': self.auction.related_property.city,
                    'district': self.auction.related_property.district,
                } if self.auction.related_property else None,
                'image_url': self.auction.featured_image_url
            }

            return auction_data
        except Exception as e:
            logger.error(f"Error getting initial auction data: {str(e)}")
            return {
                'type': 'error',
                'message': 'Failed to load auction data'
            }

    async def process_message(self, data):
        """Process messages with performance monitoring"""
        import time
        from django.conf import settings

        start_time = time.time()
        action = data.get('action')

        try:
            if action == 'get_state':
                # Send current auction state
                auction = await self.get_auction(refresh=True)
                if auction:
                    self.auction = auction  # Update stored auction

                    await self.send(text_data=json.dumps({
                        'type': 'auction_state',
                        'auction_id': str(auction.id),
                        'status': auction.status,
                        'status_display': auction.get_status_display(),
                        'current_bid': self.format_decimal(auction.current_bid),
                        'bid_count': auction.bid_count,
                        'time_remaining': auction.time_remaining,
                        'is_active': auction.is_active,
                        'end_date': self.encode_datetime(auction.end_date)
                    }))
                else:
                    await self.send_error('Auction not found')

            elif action == 'watch_auction':
                # Register that the user is watching this auction
                if self.scope['user'].is_authenticated:
                    success = await self.register_auction_watch()

                    await self.send(text_data=json.dumps({
                        'type': 'watch_status',
                        'is_watching': success
                    }))

            elif action == 'unwatch_auction':
                # Register that the user is no longer watching this auction
                if self.scope['user'].is_authenticated:
                    success = await self.unregister_auction_watch()

                    await self.send(text_data=json.dumps({
                        'type': 'watch_status',
                        'is_watching': not success
                    }))

            elif action == 'get_watch_status':
                # Check if user is watching this auction
                if self.scope['user'].is_authenticated:
                    is_watching = await self.is_watching_auction()

                    await self.send(text_data=json.dumps({
                        'type': 'watch_status',
                        'is_watching': is_watching
                    }))

        except Exception as e:
            # Enhanced error logging
            logger.error(
                f"Error in auction consumer action '{action}': {str(e)}",
                exc_info=True
            )
            await self.send_error(f"Failed to process {action}", code="auction_action_error")

        finally:
            # Performance tracking
            execution_time = time.time() - start_time
            if execution_time > 0.5 or settings.DEBUG:  # 500ms threshold
                logger.info(
                    f"WebSocket performance: {action} took {execution_time:.2f}s (auction={self.auction_id})"
                )

    # Event handlers for group messages
    async def auction_update(self, event):
        """Handle auction update event"""
        # Send the event data to the WebSocket
        await self.send(text_data=json.dumps(event))

    async def status_update(self, event):
        """Handle auction status update event"""
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': event['status'],
            'status_display': event['status_display'],
            'message': event.get('message'),
            'timestamp': event.get('timestamp', self.encode_datetime(timezone.now()))
        }))

    async def time_update(self, event):
        """Handle auction time update event"""
        await self.send(text_data=json.dumps({
            'type': 'time_update',
            'time_remaining': event['time_remaining'],
            'end_date': event['end_date'],
            'is_extended': event.get('is_extended', False),
            'timestamp': event.get('timestamp', self.encode_datetime(timezone.now()))
        }))

    async def extension_update(self, event):
        """Handle auction extension event"""
        await self.send(text_data=json.dumps({
            'type': 'extension_update',
            'new_end_date': event['new_end_date'],
            'extension_minutes': event['extension_minutes'],
            'time_remaining': event['time_remaining'],
            'reason': event.get('reason', 'New bid placed near closing time'),
            'timestamp': event.get('timestamp', self.encode_datetime(timezone.now()))
        }))

    # Database access methods
    @database_sync_to_async
    def get_auction(self, refresh=False):
        """Get auction data"""
        try:
            if refresh or not hasattr(self, 'auction'):
                return Auction.objects.get(id=self.auction_id)
            return self.auction
        except Auction.DoesNotExist:
            logger.warning(f"Auction {self.auction_id} not found")
            return None

    @database_sync_to_async
    def register_auction_watch(self):
        """Register that the user is watching this auction"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                return False

            auction = Auction.objects.get(id=self.auction_id)

            # Check if the model supports the watched_by relationship
            if hasattr(auction, 'watched_by'):
                auction.watched_by.add(user)
                return True
            else:
                # Alternative - store in auction metadata if watched_by isn't available
                if not hasattr(auction, 'metadata') or not isinstance(auction.metadata, dict):
                    auction.metadata = {}

                watchers = auction.metadata.get('watchers', [])
                if str(user.id) not in watchers:
                    watchers.append(str(user.id))
                    auction.metadata['watchers'] = watchers
                    auction.save(update_fields=['metadata'])

                return True

            return False
        except Exception as e:
            logger.error(f"Error registering auction watch: {str(e)}")
            return False

    @database_sync_to_async
    def unregister_auction_watch(self):
        """Register that the user is no longer watching this auction"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                return False

            auction = Auction.objects.get(id=self.auction_id)

            # Check if the model supports the watched_by relationship
            if hasattr(auction, 'watched_by'):
                auction.watched_by.remove(user)
                return True
            else:
                # Alternative - store in auction metadata
                if not hasattr(auction, 'metadata') or not isinstance(auction.metadata, dict):
                    return False

                watchers = auction.metadata.get('watchers', [])
                if str(user.id) in watchers:
                    watchers.remove(str(user.id))
                    auction.metadata['watchers'] = watchers
                    auction.save(update_fields=['metadata'])

                return True

            return False
        except Exception as e:
            logger.error(f"Error unregistering auction watch: {str(e)}")
            return False

    @database_sync_to_async
    def is_watching_auction(self):
        """Check if user is watching this auction"""
        try:
            user = self.scope['user']
            if not user.is_authenticated:
                return False

            auction = Auction.objects.get(id=self.auction_id)

            # Check if the model supports the watched_by relationship
            if hasattr(auction, 'watched_by'):
                return auction.watched_by.filter(id=user.id).exists()
            else:
                # Alternative - check in auction metadata
                if not hasattr(auction, 'metadata') or not isinstance(auction.metadata, dict):
                    return False

                watchers = auction.metadata.get('watchers', [])
                return str(user.id) in watchers

            return False
        except Exception as e:
            logger.error(f"Error checking auction watch status: {str(e)}")
            return False
