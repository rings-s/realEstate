import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

def send_to_group(group_name, message_type, data, additional_data=None):
    """Send a message to a channel group."""
    try:
        channel_layer = get_channel_layer()

        # Add timestamp
        if 'timestamp' not in data:
            data['timestamp'] = timezone.now().isoformat()

        # Create the message
        message = {
            'type': message_type,
            **data
        }

        # Add any additional data
        if additional_data:
            message.update(additional_data)

        # Send to the group
        async_to_sync(channel_layer.group_send)(group_name, message)
        return True
    except Exception:
        return False

def send_user_notification(user_id, notification_data):
    """Send a notification to a user."""
    return send_to_group(
        f'notifications_{user_id}',
        'notification_message',
        {'notification': notification_data}
    )

def send_auction_update(auction_id, update_type, data):
    """Send an auction update."""
    # Send to auction group
    send_to_group(
        f'auction_{auction_id}',
        'auction_update',
        {'update_type': update_type, 'data': data},
        {'auction_id': str(auction_id)}
    )

    # Also send to bidding group
    send_to_group(
        f'bidding_{auction_id}',
        'bidding_update',
        {'update_type': update_type, 'data': data}
    )

def broadcast_bid_placed(auction_id, bid_data, seller_id, bidder_ids=None):
    """Broadcast a bid placed event to all relevant parties."""
    # Send to auction and bidding groups
    send_auction_update(auction_id, 'bid_placed', bid_data)

    # Send to seller
    if seller_id:
        send_user_notification(seller_id, {
            'type': 'bid_placed',
            'title': 'New bid received',
            'auction_id': auction_id,
            'bid_data': bid_data
        })

    # Send to outbid bidders
    if bidder_ids:
        for bidder_id in bidder_ids:
            send_user_notification(bidder_id, {
                'type': 'outbid',
                'title': 'You have been outbid',
                'auction_id': auction_id,
                'bid_data': bid_data
            })
