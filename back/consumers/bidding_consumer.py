# consumers/bidding_consumer.py

import json
from channels.db import database_sync_to_async
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from .base_consumer import BaseConsumer
from base.models import Auction, Bid, Notification

User = get_user_model()

class BiddingConsumer(BaseConsumer):
    """
    WebSocket consumer for real-time auction bidding.
    Provides bid placement, bid updates, and auction status changes.
    """
    group_prefix = 'bidding'
    
    async def get_group_name(self):
        """Get the group name based on the auction ID"""
        self.auction_id = self.params.get('auction_id')
        return f'bidding_{self.auction_id}'
    
    async def authenticate(self):
        """Basic authentication - verify auction exists and is active"""
        auction = await self.get_auction()
        if not auction:
            return False
            
        # Store auction for later use
        self.auction = auction
        return True
    
    async def get_initial_data(self):
        """Get initial bidding data to send on connect"""
        try:
            # Get recent bids for this auction
            recent_bids = await self.get_recent_bids()
            
            # Get auction information
            auction_data = {
                'id': str(self.auction.id),
                'title': self.auction.title,
                'current_bid': self.format_decimal(self.auction.current_bid),
                'min_bid_increment': self.format_decimal(self.auction.min_bid_increment),
                'status': self.auction.status,
                'status_display': self.auction.get_status_display(),
                'end_date': self.encode_datetime(self.auction.end_date),
                'time_remaining': self.auction.time_remaining,
                'bid_count': self.auction.bid_count,
                'is_active': self.auction.is_active
            }
            
            return {
                'type': 'bidding_init',
                'auction': auction_data,
                'recent_bids': recent_bids
            }
        except Exception as e:
            self.logger.error(f"Error getting initial bidding data: {str(e)}")
            return {
                'type': 'error',
                'message': 'Failed to load bidding data'
            }
    
    async def process_message(self, data):
        """Process messages from the client"""
        action = data.get('action')
        
        if action == 'place_bid':
            # Get bid details
            amount = data.get('amount')
            auto_bid_limit = data.get('auto_bid_limit')
            user_id = data.get('user_id')
            client_id = data.get('client_id', '')  # For optimistic UI updates
            
            # Validate amount
            if not amount:
                await self.send_error('Bid amount is required', client_id=client_id)
                return
                
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                await self.send_error('Invalid bid amount', client_id=client_id)
                return
                
            # Validate auto_bid_limit if provided
            if auto_bid_limit:
                try:
                    auto_bid_limit = float(auto_bid_limit)
                    if auto_bid_limit <= amount:
                        await self.send_error('Auto-bid limit must be greater than bid amount', client_id=client_id)
                        return
                except (ValueError, TypeError):
                    await self.send_error('Invalid auto-bid limit', client_id=client_id)
                    return
            
            # Verify user_id
            if not user_id:
                await self.send_error('User ID is required', client_id=client_id)
                return
                
            # Place bid
            bid, error = await self.place_bid(user_id, amount, auto_bid_limit, client_id)
            
            if error:
                await self.send_error(error, client_id=client_id)
                return
                
            if bid:
                # Notify all clients about new bid
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'new_bid_message',
                        'bid': bid
                    }
                )
                
                # Notify the auction group about price update
                auction = await self.get_auction()  # Get updated auction data
                
                if auction:
                    # Send to auction consumer group
                    await self.channel_layer.group_send(
                        f'auction_{self.auction_id}',
                        {
                            'type': 'auction_update',
                            'auction_id': self.auction_id,
                            'update_type': 'price_update',
                            'data': {
                                'current_bid': self.format_decimal(auction.current_bid),
                                'bid_count': auction.bid_count,
                                'highest_bidder': bid.get('bidder'),
                                'timestamp': self.encode_datetime(timezone.now())
                            }
                        }
                    )
        
        elif action == 'get_recent_bids':
            # Get recent bids
            limit = data.get('limit', 10)
            recent_bids = await self.get_recent_bids(limit)
            
            await self.send(text_data=json.dumps({
                'type': 'recent_bids',
                'bids': recent_bids
            }))
            
        elif action == 'get_bid_history':
            # Get complete bid history with pagination
            page = data.get('page', 1)
            page_size = data.get('page_size', 20)
            
            bids, total_pages = await self.get_bid_history(page, page_size)
            
            await self.send(text_data=json.dumps({
                'type': 'bid_history',
                'bids': bids,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            }))
    
    # Event handlers for group messages
    async def new_bid_message(self, event):
        """Handle new bid event"""
        await self.send(text_data=json.dumps({
            'type': 'new_bid',
            'bid': event['bid']
        }))
    
    async def auction_status_update(self, event):
        """Handle auction status update event"""
        await self.send(text_data=json.dumps({
            'type': 'auction_status',
            'status': event['status'],
            'status_display': event['status_display'],
            'message': event.get('message'),
            'timestamp': event.get('timestamp', self.encode_datetime(timezone.now()))
        }))
    
    async def bidding_update(self, event):
        """Handle generic bidding update event"""
        await self.send(text_data=json.dumps({
            'type': 'bidding_update',
            'update_type': event['update_type'],
            'data': event['data']
        }))
    
    # Database access methods
    @database_sync_to_async
    def get_auction(self):
        """Get auction data"""
        try:
            return Auction.objects.get(id=self.auction_id)
        except Auction.DoesNotExist:
            self.logger.warning(f"Auction {self.auction_id} not found")
            return None
    
    @database_sync_to_async
    def get_recent_bids(self, limit=10):
        """Get recent bids for this auction"""
        try:
            bids = Bid.objects.filter(
                auction_id=self.auction_id
            ).select_related('bidder').order_by('-bid_time')[:limit]
            
            # Convert to dict for JSON serialization
            return [
                {
                    'id': str(bid.id),
                    'auction': str(bid.auction.id),
                    'bidder': {
                        'id': str(bid.bidder.id),
                        'name': f"{bid.bidder.first_name} {bid.bidder.last_name}".strip() or bid.bidder.email
                    },
                    'bid_amount': self.format_decimal(bid.bid_amount),
                    'is_auto_bid': bid.is_auto_bid,
                    'status': bid.status,
                    'status_display': bid.get_status_display(),
                    'bid_time': self.encode_datetime(bid.bid_time),
                    'created_at': self.encode_datetime(bid.created_at)
                }
                for bid in bids
            ]
        except Exception as e:
            self.logger.error(f"Error getting recent bids: {str(e)}")
            return []
    
    @database_sync_to_async
    def get_bid_history(self, page=1, page_size=20):
        """Get paginated bid history"""
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count for pagination
            total_bids = Bid.objects.filter(auction_id=self.auction_id).count()
            total_pages = (total_bids + page_size - 1) // page_size  # Ceiling division
            
            # Get bids for this page
            bids = Bid.objects.filter(
                auction_id=self.auction_id
            ).select_related('bidder').order_by('-bid_time')[offset:offset+page_size]
            
            # Convert to dict for JSON serialization
            return [
                {
                    'id': str(bid.id),
                    'auction': str(bid.auction.id),
                    'bidder': {
                        'id': str(bid.bidder.id),
                        'name': f"{bid.bidder.first_name} {bid.bidder.last_name}".strip() or bid.bidder.email
                    },
                    'bid_amount': self.format_decimal(bid.bid_amount),
                    'is_auto_bid': bid.is_auto_bid,
                    'status': bid.status,
                    'status_display': bid.get_status_display(),
                    'bid_time': self.encode_datetime(bid.bid_time),
                    'created_at': self.encode_datetime(bid.created_at)
                }
                for bid in bids
            ], total_pages
        except Exception as e:
            self.logger.error(f"Error getting bid history: {str(e)}")
            return [], 0
    
    @database_sync_to_async
    def place_bid(self, user_id, amount, auto_bid_limit=None, client_id=None):
        """Place a new bid"""
        try:
            # Get user
            user = User.objects.get(id=user_id)
            
            # Refresh auction data
            auction = Auction.objects.get(id=self.auction_id)
            
            # Validation checks
            if auction.status != 'active':
                return None, "Auction is not active"
                
            if not auction.is_active:
                return None, "Auction is not currently running"
                
            # Ensure bid is higher than current bid + minimum increment
            min_bid = auction.current_bid + auction.min_bid_increment
            if amount < min_bid:
                return None, f"Bid must be at least {min_bid}"
                
            # Check if user is the seller (can't bid on own auction)
            if user.id == auction.related_property.owner.id:
                return None, "You cannot bid on your own auction"
            
            # Create bid using transaction to ensure consistency
            with transaction.atomic():
                # Get client IP from WebSocket scope if available
                client_ip = self.scope.get('client', [None])[0]
                if not client_ip:
                    client_ip = '0.0.0.0'  # Fallback
                
                # Create the bid
                bid = Bid.objects.create(
                    auction=auction,
                    bidder=user,
                    bid_amount=amount,
                    max_bid_amount=auto_bid_limit,
                    status='pending',
                    is_auto_bid=bool(auto_bid_limit),
                    ip_address=client_ip,
                    user_agent=self.scope.get('headers', {}).get('user-agent', 'Unknown'),
                    bid_time=timezone.now()
                )
                
                # Update auction's current bid
                auction.current_bid = amount
                auction.save(update_fields=['current_bid', 'updated_at'])
                
                # Find and update the status of the previous winning bid
                previous_winning = Bid.objects.filter(
                    auction=auction,
                    status='winning'
                ).first()
                
                if previous_winning:
                    previous_winning.status = 'outbid'
                    previous_winning.save(update_fields=['status', 'updated_at'])
                    
                    # Create notification for outbid user
                    self.create_outbid_notification(previous_winning, bid)
                
                # Set this bid as winning
                bid.status = 'winning'
                bid.save(update_fields=['status'])
                
                # Create notification for seller
                self.create_new_bid_notification(bid)
                
                # Return bid data for WebSocket response
                return {
                    'id': str(bid.id),
                    'auction': str(bid.auction.id),
                    'bidder': {
                        'id': str(bid.bidder.id),
                        'name': f"{bid.bidder.first_name} {bid.bidder.last_name}".strip() or bid.bidder.email
                    },
                    'bid_amount': self.format_decimal(bid.bid_amount),
                    'is_auto_bid': bid.is_auto_bid,
                    'status': bid.status,
                    'status_display': bid.get_status_display(),
                    'bid_time': self.encode_datetime(bid.bid_time),
                    'created_at': self.encode_datetime(bid.created_at),
                    'client_id': client_id
                }, None
        except User.DoesNotExist:
            return None, "User not found"
        except Auction.DoesNotExist:
            return None, "Auction not found"
        except Exception as e:
            self.logger.error(f"Error placing bid: {str(e)}")
            return None, f"Error placing bid: {str(e)}"
    
    def create_outbid_notification(self, previous_bid, new_bid):
        """Create notification for outbid user"""
        try:
            Notification.objects.create(
                recipient=previous_bid.bidder,
                notification_type='outbid',
                title='You have been outbid',
                content=f'Your bid of {previous_bid.bid_amount} on {previous_bid.auction.title} has been outbid.',
                channel='app',
                related_auction=previous_bid.auction,
                related_bid=previous_bid,
                is_read=False,
                is_sent=True,
                sent_at=timezone.now(),
                icon='dollar-sign',
                color='warning',
                action_url=f'/auctions/{previous_bid.auction.id}'
            )
        except Exception as e:
            self.logger.error(f"Error creating outbid notification: {str(e)}")
    
    def create_new_bid_notification(self, bid):
        """Create notification for auction seller"""
        try:
            Notification.objects.create(
                recipient=bid.auction.related_property.owner,
                notification_type='new_bid',
                title='New bid received',
                content=f'Your auction {bid.auction.title} received a new bid of {bid.bid_amount}.',
                channel='app',
                related_auction=bid.auction,
                related_bid=bid,
                is_read=False,
                is_sent=True,
                sent_at=timezone.now(),
                icon='gavel',
                color='success',
                action_url=f'/auctions/{bid.auction.id}'
            )
        except Exception as e:
            self.logger.error(f"Error creating new bid notification: {str(e)}")