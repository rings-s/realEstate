# consumers/utils.py
import json
import logging
import uuid
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)

class EnhancedJSONEncoder(DjangoJSONEncoder):
    """Enhanced JSON encoder that handles additional types"""
    def default(self, obj):
        # Handle UUID objects
        if hasattr(obj, 'hex'):
            return str(obj)
        return super().default(obj)

def generate_request_id():
    """Generate a unique request ID for tracking"""
    return str(uuid.uuid4())

def send_user_notification(user_id, notification_data, request_id=None):
    """
    Send a notification to a specific user via WebSocket with enhanced tracking and error handling
    
    Args:
        user_id: The ID of the user to send the notification to
        notification_data: The notification data to send
        request_id: Optional tracking ID for logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not request_id:
        request_id = generate_request_id()
        
    # Start performance timing
    start_time = time.time()
    
    try:
        channel_layer = get_channel_layer()
        
        # Add timestamp if not present
        if 'timestamp' not in notification_data:
            notification_data['timestamp'] = timezone.now().isoformat()
            
        # Add request ID for tracking
        notification_data['request_id'] = request_id
        
        # Convert notification_data to a serializable format if needed
        # This ensures UUIDs, dates, and other Django model-specific types are properly serialized
        serialized_data = json.loads(json.dumps(notification_data, cls=EnhancedJSONEncoder))
        
        # Log the notification being sent
        logger.info(
            f"[{request_id}] Sending notification to user {user_id}: "
            f"type={serialized_data.get('type', 'unknown')}"
        )
        
        # Send to user's notification group
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'notification_message',
                'notification': serialized_data,
                'request_id': request_id
            }
        )
        
        # Also send to user's dashboard if they are viewing it
        async_to_sync(channel_layer.group_send)(
            f'dashboard_{user_id}',
            {
                'type': 'notification_event',
                'notification': serialized_data,
                'request_id': request_id
            }
        )
        
        # Log performance metrics
        execution_time = time.time() - start_time
        if execution_time > 0.5:  # Log slow operations (>500ms)
            logger.warning(
                f"[{request_id}] Slow notification delivery: {execution_time:.2f}s "
                f"to user {user_id}"
            )
        
        return True
    except Exception as e:
        logger.exception(f"[{request_id}] Error sending WebSocket notification to user {user_id}: {e}")
        return False

def send_auction_update(auction_id, update_type, data, request_id=None):
    """
    Send an update about an auction with improved error handling and tracking
    
    Args:
        auction_id: The ID of the auction
        update_type: The type of update (e.g., 'price_update', 'status_update')
        data: The update data
        request_id: Optional tracking ID for logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not request_id:
        request_id = generate_request_id()
        
    # Start performance timing
    start_time = time.time()
    
    try:
        channel_layer = get_channel_layer()
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = timezone.now().isoformat()
            
        # Add request ID for tracking
        data['request_id'] = request_id
        
        # Convert data to a serializable format if needed
        serialized_data = json.loads(json.dumps(data, cls=EnhancedJSONEncoder))
        
        # Log the auction update being sent
        logger.info(
            f"[{request_id}] Sending auction update for auction {auction_id}: "
            f"type={update_type}"
        )
        
        # Send to auction group
        auction_message = {
            'type': 'auction_update',
            'auction_id': str(auction_id),
            'update_type': update_type,
            'data': serialized_data,
            'request_id': request_id
        }
        async_to_sync(channel_layer.group_send)(f'auction_{auction_id}', auction_message)
        
        # Send to bidding group as well
        bidding_message = {
            'type': 'bidding_update',
            'update_type': update_type,
            'data': serialized_data,
            'request_id': request_id
        }
        async_to_sync(channel_layer.group_send)(f'bidding_{auction_id}', bidding_message)
        
        # Log performance metrics
        execution_time = time.time() - start_time
        if execution_time > 0.5:  # Log slow operations (>500ms)
            logger.warning(
                f"[{request_id}] Slow auction update delivery: {execution_time:.2f}s "
                f"for auction {auction_id}, type {update_type}"
            )
        
        return True
    except Exception as e:
        logger.exception(f"[{request_id}] Error sending auction update for auction {auction_id}: {e}")
        return False

def send_chat_message(room_name, message_data, request_id=None):
    """
    Send a chat message to a room with improved error handling and tracking
    
    Args:
        room_name: The name of the chat room
        message_data: The message data to send
        request_id: Optional tracking ID for logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not request_id:
        request_id = generate_request_id()
        
    # Start performance timing
    start_time = time.time()
    
    try:
        channel_layer = get_channel_layer()
        
        # Add timestamp if not present
        if 'timestamp' not in message_data:
            message_data['timestamp'] = timezone.now().isoformat()
        
        # Add request ID for tracking
        message_data['request_id'] = request_id
        
        # Add type if not present
        if 'type' not in message_data:
            message_data['type'] = 'chat_message'
            
        # Convert message data to a serializable format if needed
        serialized_data = json.loads(json.dumps(message_data, cls=EnhancedJSONEncoder))
        
        # Log the chat message being sent
        message_snippet = serialized_data.get('message', '')[:50]
        if len(message_snippet) < len(serialized_data.get('message', '')):
            message_snippet += '...'
            
        logger.info(
            f"[{request_id}] Sending chat message to room {room_name}: "
            f"type={serialized_data.get('type')}, content=\"{message_snippet}\""
        )
        
        # Send to chat room group
        async_to_sync(channel_layer.group_send)(f'chat_{room_name}', serialized_data)
        
        # Log performance metrics
        execution_time = time.time() - start_time
        if execution_time > 0.5:  # Log slow operations (>500ms)
            logger.warning(
                f"[{request_id}] Slow chat message delivery: {execution_time:.2f}s "
                f"to room {room_name}"
            )
        
        return True
    except Exception as e:
        logger.exception(f"[{request_id}] Error sending chat message to room {room_name}: {e}")
        return False

def send_dashboard_update(user_id, update_type, data, request_id=None):
    """
    Send a dashboard update to a user with improved error handling and tracking
    
    Args:
        user_id: The ID of the user
        update_type: The type of update (e.g., 'auction_update', 'bid_update')
        data: The update data
        request_id: Optional tracking ID for logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not request_id:
        request_id = generate_request_id()
        
    # Start performance timing
    start_time = time.time()
    
    try:
        channel_layer = get_channel_layer()
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = timezone.now().isoformat()
            
        # Add request ID for tracking
        data['request_id'] = request_id
        
        # Convert data to a serializable format if needed
        serialized_data = json.loads(json.dumps(data, cls=EnhancedJSONEncoder))
        
        # Log the dashboard update being sent
        logger.info(
            f"[{request_id}] Sending dashboard update to user {user_id}: "
            f"type={update_type}"
        )
        
        # Send to dashboard group
        async_to_sync(channel_layer.group_send)(
            f'dashboard_{user_id}',
            {
                'type': 'dashboard_update',
                'update_type': update_type,
                'data': serialized_data,
                'request_id': request_id
            }
        )
        
        # Log performance metrics
        execution_time = time.time() - start_time
        if execution_time > 0.5:  # Log slow operations (>500ms)
            logger.warning(
                f"[{request_id}] Slow dashboard update delivery: {execution_time:.2f}s "
                f"to user {user_id}, type {update_type}"
            )
        
        return True
    except Exception as e:
        logger.exception(f"[{request_id}] Error sending dashboard update to user {user_id}: {e}")
        return False

def broadcast_auction_event(auction_id, event_type, event_data, request_id=None):
    """
    Broadcast an auction event to all relevant WebSocket groups and users
    
    This is a convenience function that sends updates to:
    1. The auction's WebSocket group
    2. The bidding WebSocket group
    3. The seller's dashboard
    4. All active bidders' dashboards
    
    Args:
        auction_id: The ID of the auction
        event_type: The type of event (e.g., 'bid_placed', 'auction_ended')
        event_data: The event data
        request_id: Optional tracking ID for logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not request_id:
        request_id = generate_request_id()
    
    success = True
    
    # Send to auction and bidding groups
    if not send_auction_update(auction_id, event_type, event_data, request_id):
        success = False
    
    # If the event data contains user IDs for seller and bidders, send to their dashboards
    seller_id = event_data.get('seller_id')
    if seller_id:
        if not send_dashboard_update(seller_id, f'auction_{event_type}', event_data, request_id):
            success = False
    
    # Send to active bidders if provided
    bidder_ids = event_data.get('bidder_ids', [])
    for bidder_id in bidder_ids:
        if not send_dashboard_update(bidder_id, f'auction_{event_type}', event_data, request_id):
            success = False
    
    return success