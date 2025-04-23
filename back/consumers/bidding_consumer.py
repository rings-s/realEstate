from channels.db import database_sync_to_async
from django.utils import timezone
from django.db import transaction

from .base_consumer import BaseConsumer
from base.models import Auction, Bid, Notification

class BiddingConsumer(BaseConsumer):
    """WebSocket consumer for real-time auction bidding."""
    group_prefix = 'bidding'

    async def get_group_name(self):
        self.auction_id = self.params.get('auction_id')
        return f'bidding_{self.auction_id}'

    async def authenticate(self):
        auction = await self.get_auction()
        if not auction:
            return False
        self.auction = auction
        return True

    async def get_initial_data(self):
        try:
            recent_bids = await self.get_recent_bids()
            return {
                'type': 'bidding_init',
                'auction': {
                    'id': str(self.auction.id),
                    'title': self.auction.title,
                    'current_bid': self.format_decimal(self.auction.current_bid),
                    'min_bid_increment': self.format_decimal(self.auction.minimum_increment),
                    'status': self.auction.status,
                    'end_date': self.encode_datetime(self.auction.end_date),
                    'time_remaining': self.auction.time_remaining,
                    'bid_count': self.auction.bid_count
                },
                'recent_bids': recent_bids
            }
        except Exception as e:
            return {'type': 'error', 'message': 'Failed to load bidding data'}

    async def process_message(self, data):
        action = data.get('action')

        if action == 'place_bid':
            amount = data.get('amount')
            auto_bid_limit = data.get('auto_bid_limit')
            user_id = data.get('user_id')
            client_id = data.get('client_id', '')

            if not amount or not user_id:
                await self.send_error('Bid amount and user ID are required', client_id=client_id)
                return

            try:
                amount = float(amount)
                if auto_bid_limit:
                    auto_bid_limit = float(auto_bid_limit)
                    if auto_bid_limit <= amount:
                        await self.send_error('Auto-bid limit must be greater than bid amount', client_id=client_id)
                        return
            except (ValueError, TypeError):
                await self.send_error('Invalid bid amount or auto-bid limit', client_id=client_id)
                return

            bid, error = await self.place_bid(user_id, amount, auto_bid_limit, client_id)

            if error:
                await self.send_error(error, client_id=client_id)
                return

            if bid:
                await self.channel_layer.group_send(
                    self.group_name,
                    {'type': 'new_bid_message', 'bid': bid}
                )

                auction = await self.get_auction()
                if auction:
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
            limit = data.get('limit', 10)
            recent_bids = await self.get_recent_bids(limit)
            await self.send(text_data=json.dumps({'type': 'recent_bids', 'bids': recent_bids}))

        elif action == 'get_bid_history':
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

    # Event handlers
    async def new_bid_message(self, event):
        await self.send(text_data=json.dumps({'type': 'new_bid', 'bid': event['bid']}))

    # Database methods
    @database_sync_to_async
    def get_auction(self):
        try:
            return Auction.objects.get(id=self.auction_id)
        except Auction.DoesNotExist:
            return None

    @database_sync_to_async
    def get_recent_bids(self, limit=10):
        try:
            bids = Bid.objects.filter(auction_id=self.auction_id).select_related('bidder').order_by('-bid_time')[:limit]
            return [
                {
                    'id': str(bid.id),
                    'bidder': {
                        'id': str(bid.bidder.id),
                        'name': f"{bid.bidder.first_name} {bid.bidder.last_name}".strip() or bid.bidder.email
                    },
                    'bid_amount': self.format_decimal(bid.bid_amount),
                    'is_auto_bid': bid.is_auto_bid,
                    'status': bid.status,
                    'bid_time': self.encode_datetime(bid.bid_time)
                }
                for bid in bids
            ]
        except Exception:
            return []

    @database_sync_to_async
    def place_bid(self, user_id, amount, auto_bid_limit=None, client_id=None):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(id=user_id)
            auction = Auction.objects.get(id=self.auction_id)

            if auction.status != 'active':
                return None, "Auction is not active"

            # Ensure bid is higher than current bid + minimum increment
            min_bid = auction.current_bid + auction.minimum_increment
            if amount < min_bid:
                return None, f"Bid must be at least {min_bid}"

            if user.id == auction.related_property.owner.id:
                return None, "You cannot bid on your own auction"

            with transaction.atomic():
                # Create the bid
                bid = Bid.objects.create(
                    auction=auction,
                    bidder=user,
                    bid_amount=amount,
                    is_auto_bid=bool(auto_bid_limit),
                    status='pending',
                    bid_time=timezone.now()
                )

                # Update auction
                auction.current_bid = amount
                auction.save(update_fields=['current_bid'])

                # Update previous winning bid
                prev_winning = Bid.objects.filter(auction=auction, status='winning').first()
                if prev_winning:
                    prev_winning.status = 'outbid'
                    prev_winning.save(update_fields=['status'])

                # Set this as winning
                bid.status = 'winning'
                bid.save(update_fields=['status'])

                return {
                    'id': str(bid.id),
                    'bidder': {
                        'id': str(bid.bidder.id),
                        'name': f"{bid.bidder.first_name} {bid.bidder.last_name}".strip() or bid.bidder.email
                    },
                    'bid_amount': self.format_decimal(bid.bid_amount),
                    'is_auto_bid': bid.is_auto_bid,
                    'status': bid.status,
                    'bid_time': self.encode_datetime(bid.bid_time),
                    'client_id': client_id
                }, None
        except Exception as e:
            return None, f"Error placing bid: {str(e)}"
