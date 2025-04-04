# consumers/notification_consumer.py

import json
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from .base_consumer import BaseConsumer
from base.models import Notification

class NotificationConsumer(BaseConsumer):
    """
    WebSocket consumer for real-time notification updates.
    Handles new notifications, marking notifications as read,
    and notification delivery status updates.
    """
    group_prefix = 'notifications'
    
    async def authenticate(self):
        """Ensure the user is authenticated and authorized to receive these notifications"""
        user = self.scope.get('user')
        requested_user_id = self.params.get('user_id')
        
        if not user or not user.is_authenticated:
            return False
            
        # Users can only access their own notifications
        if str(user.id) != requested_user_id:
            return False
            
        return True
    
    async def get_initial_data(self):
        """Get initial notification data to send on connect"""
        try:
            notifications = await self.get_notifications()
            return {
                'type': 'notifications',
                'notifications': notifications
            }
        except Exception as e:
            self.logger.error(f"Error getting initial notifications: {str(e)}")
            return {
                'type': 'error',
                'message': 'Failed to load notifications'
            }
    
    async def process_message(self, data):
        """Process messages from the client"""
        action = data.get('action')
        
        if action == 'mark_read':
            notification_id = data.get('notification_id')
            if notification_id:
                success = await self.mark_notification_read(notification_id)
                await self.send(text_data=json.dumps({
                    'type': 'notification_read',
                    'notification_id': notification_id,
                    'success': success
                }))
                
                # Also broadcast to other connected clients for this user
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'notification_read_event',
                        'notification_id': notification_id
                    }
                )
            else:
                await self.send_error('Missing notification_id')
                
        elif action == 'mark_all_read':
            success = await self.mark_all_notifications_read()
            await self.send(text_data=json.dumps({
                'type': 'all_read',
                'success': success
            }))
            
            # Also broadcast to other connected clients for this user
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'all_read_event',
                }
            )
            
        elif action == 'mark_displayed':
            notification_id = data.get('notification_id')
            if notification_id:
                await self.mark_notification_displayed(notification_id)
            else:
                await self.send_error('Missing notification_id')
                
        elif action == 'get_notifications':
            # Get notifications with optional parameters
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)
            
            notifications = await self.get_notifications(limit, offset)
            await self.send(text_data=json.dumps({
                'type': 'notifications',
                'notifications': notifications
            }))
            
        elif action == 'get_unread_count':
            # Get unread notifications count
            count = await self.get_unread_count()
            await self.send(text_data=json.dumps({
                'type': 'unread_count',
                'count': count
            }))
    
    # Event handlers for group messages
    async def notification_message(self, event):
        """Handle new notification event"""
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification']
        }))
    
    async def notification_read_event(self, event):
        """Handle notification read event"""
        await self.send(text_data=json.dumps({
            'type': 'notification_read',
            'notification_id': event['notification_id']
        }))
    
    async def all_read_event(self, event):
        """Handle all notifications read event"""
        await self.send(text_data=json.dumps({
            'type': 'all_read'
        }))
        
    async def notification_deleted_event(self, event):
        """Handle notification deletion event"""
        await self.send(text_data=json.dumps({
            'type': 'notification_deleted',
            'notification_id': event['notification_id']
        }))
    
    # Database access methods
    @database_sync_to_async
    def get_notifications(self, limit=50, offset=0):
        """Get notifications for the user with pagination"""
        try:
            user_id = self.params.get('user_id')
            
            notifications = Notification.objects.filter(
                recipient_id=user_id
            ).order_by('-created_at')[offset:offset+limit]
            
            # Convert to dict for JSON serialization
            return [
                {
                    'id': str(notification.id),
                    'title': notification.title,
                    'content': notification.content,
                    'notification_type': notification.notification_type,
                    'notification_type_display': notification.get_notification_type_display(),
                    'channel': notification.channel,
                    'channel_display': notification.get_channel_display(),
                    'related_property_id': str(notification.related_property.id) if notification.related_property else None,
                    'related_auction_id': str(notification.related_auction.id) if notification.related_auction else None,
                    'related_bid_id': str(notification.related_bid.id) if notification.related_bid else None,
                    'related_contract_id': str(notification.related_contract.id) if notification.related_contract else None,
                    'related_payment_id': str(notification.related_payment.id) if notification.related_payment else None,
                    'related_message_id': str(notification.related_message.id) if notification.related_message else None,
                    'is_read': notification.is_read,
                    'read_at': self.encode_datetime(notification.read_at),
                    'is_sent': notification.is_sent,
                    'sent_at': self.encode_datetime(notification.sent_at),
                    'icon': notification.icon,
                    'color': notification.color,
                    'action_url': notification.action_url,
                    'created_at': self.encode_datetime(notification.created_at)
                }
                for notification in notifications
            ]
        except Exception as e:
            self.logger.error(f"Error getting notifications: {str(e)}")
            return []
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notifications count"""
        try:
            user_id = self.params.get('user_id')
            return Notification.objects.filter(recipient_id=user_id, is_read=False).count()
        except Exception as e:
            self.logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        try:
            user_id = self.params.get('user_id')
            
            notification = Notification.objects.get(
                id=notification_id,
                recipient_id=user_id
            )
            
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save(update_fields=['is_read', 'read_at', 'updated_at'])
            
            return True
        except ObjectDoesNotExist:
            self.logger.warning(f"Notification {notification_id} not found for user {user_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error marking notification read: {str(e)}")
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read"""
        try:
            user_id = self.params.get('user_id')
            
            # Get current time
            now = timezone.now()
            
            # Update all unread notifications
            updated = Notification.objects.filter(
                recipient_id=user_id,
                is_read=False
            ).update(is_read=True, read_at=now, updated_at=now)
            
            return updated > 0  # Return True if at least one was updated
        except Exception as e:
            self.logger.error(f"Error marking all notifications read: {str(e)}")
            return False
    
    @database_sync_to_async
    def mark_notification_displayed(self, notification_id):
        """Mark a notification as displayed (seen by the user)"""
        try:
            user_id = self.params.get('user_id')
            
            # This is an optional field that may not be in the model,
            # so we'll check if it exists first
            try:
                notification = Notification.objects.get(
                    id=notification_id,
                    recipient_id=user_id
                )
                
                # Only update if the model has this field
                if hasattr(notification, 'displayed'):
                    notification.displayed = True
                    notification.save(update_fields=['displayed', 'updated_at'])
                
                return True
            except ObjectDoesNotExist:
                self.logger.warning(f"Notification {notification_id} not found for user {user_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error marking notification displayed: {str(e)}")
            return False