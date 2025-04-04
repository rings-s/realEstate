# consumers/chat_consumer.py

import json
import re
import logging
from channels.db import database_sync_to_async
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .base_consumer import BaseConsumer
from base.models import Message, MessageThread, ThreadParticipant

logger = logging.getLogger(__name__)


class ChatConsumer(BaseConsumer):
    """
    WebSocket consumer for real-time chat messaging.
    Handles message sending, delivery status updates, and typing indicators.
    """
    group_prefix = 'chat'
    
    async def get_group_name(self):
        """Get the group name based on the room name parameter"""
        self.room_name = self.params.get('room_name')
        
        # Validate room name
        if not self._validate_room_name(self.room_name):
            logger.warning(f"Invalid room name: {self.room_name}")
            await self.close(code=4000)  # Custom code for invalid room
            return None
            
        return f'chat_{self.room_name}'
    
    async def authenticate(self):
        """Ensure the user is authenticated and has access to this chat room"""
        self.user = self.scope.get('user')
        
        # Check if user is authenticated
        if not self.user or not self.user.is_authenticated:
            # For public chats, we might allow anonymous access
            # but we'll mark them differently
            self.is_anonymous = True
            return True
        
        self.is_anonymous = False
        
        # For private chats, check if user is a participant
        # by parsing the room name to get thread ID
        if self.room_name.startswith('thread_'):
            try:
                thread_id = self.room_name.split('_')[1]
                has_access = await self.check_thread_access(thread_id)
                return has_access
            except Exception as e:
                logger.error(f"Error checking thread access: {str(e)}")
                return False
                
        # For public rooms, anyone can join
        return True
    
    async def connect(self):
        """Handle connection setup and initial data"""
        await super().connect()
        
        # If connection was accepted, send join message
        if hasattr(self, 'group_name') and self.group_name:
            # Send join message to room if authenticated
            if self.user and not self.is_anonymous:
                username = self.user.first_name or self.user.email.split('@')[0]
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'system_message',
                        'message': f"{username} joined the chat",
                        'event': 'join'
                    }
                )
    
    async def on_disconnect(self, close_code):
        """Handle disconnection and cleanup"""
        # Send leave message if user was authenticated
        if hasattr(self, 'user') and self.user and not self.is_anonymous:
            username = self.user.first_name or self.user.email.split('@')[0]
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'system_message',
                    'message': f"{username} left the chat",
                    'event': 'leave'
                }
            )
    
    async def get_initial_data(self):
        """Get initial chat history to send on connect"""
        try:
            # Get recent messages for this room/thread
            messages = await self.get_recent_messages()
            
            # For private threads, also send thread metadata
            if self.room_name.startswith('thread_'):
                thread_id = self.room_name.split('_')[1]
                thread_info = await self.get_thread_info(thread_id)
                
                return {
                    'type': 'chat_history',
                    'messages': messages,
                    'thread': thread_info
                }
            else:
                return {
                    'type': 'chat_history',
                    'messages': messages
                }
        except Exception as e:
            logger.error(f"Error getting initial chat data: {str(e)}")
            return {
                'type': 'error',
                'message': 'Failed to load chat history'
            }
    
    async def process_message(self, data):
        """Process messages from the client"""
        message_type = data.get('type')
        
        if message_type == 'message':
            # Handle chat message
            await self.handle_chat_message(data)
            
        elif message_type == 'typing':
            # Handle typing indicator
            is_typing = data.get('is_typing', False)
            await self.send_typing_indicator(is_typing)
            
        elif message_type == 'read_receipt':
            # Handle read receipt
            message_id = data.get('message_id')
            if message_id:
                await self.mark_message_read(message_id)
                
        elif message_type == 'load_more':
            # Load more message history
            before_id = data.get('before_id')
            limit = data.get('limit', 20)
            
            messages = await self.get_messages_before(before_id, limit)
            await self.send(text_data=json.dumps({
                'type': 'message_history',
                'messages': messages,
                'has_more': len(messages) == limit
            }))
    
    async def handle_chat_message(self, data):
        """Process and save an incoming chat message"""
        message_text = data.get('message', '')
        client_id = data.get('client_id', '')  # For optimistic UI updates
        
        # Validate message content
        if not message_text or not message_text.strip():
            await self.send_error('Message cannot be empty', client_id=client_id)
            return
            
        if len(message_text) > 5000:  # Limit message length
            await self.send_error('Message is too long (max 5000 characters)', client_id=client_id)
            return
        
        # Process message based on room type
        if self.room_name.startswith('thread_'):
            # Private message thread
            thread_id = self.room_name.split('_')[1]
            message_id = await self.save_thread_message(thread_id, message_text)
        else:
            # Public chat room
            message_id = await self.save_chat_message(message_text)
        
        if not message_id:
            await self.send_error('Failed to save message', client_id=client_id)
            return
            
        # Get username for display
        if self.user and not self.is_anonymous:
            username = self.user.first_name or self.user.email.split('@')[0]
            user_id = str(self.user.id)
        else:
            username = 'Anonymous'
            user_id = None
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'user_id': user_id,
                'username': username,
                'id': message_id,
                'client_id': client_id,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def send_typing_indicator(self, is_typing):
        """Send typing indicator to the room"""
        if not self.user or self.is_anonymous:
            return
            
        username = self.user.first_name or self.user.email.split('@')[0]
        user_id = str(self.user.id)
        
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'typing_indicator',
                'user_id': user_id,
                'username': username,
                'is_typing': is_typing
            }
        )
    
    # Event handlers for group messages
    async def chat_message(self, event):
        """Handle chat message event"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'user_id': event['user_id'],
            'username': event['username'],
            'id': event.get('id'),
            'client_id': event.get('client_id', ''),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))
    
    async def system_message(self, event):
        """Handle system message event (join/leave)"""
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': event['message'],
            'event': event['event'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def typing_indicator(self, event):
        """Handle typing indicator event"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    async def read_receipt(self, event):
        """Handle read receipt event"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    
    # Database access methods
    @database_sync_to_async
    def check_thread_access(self, thread_id):
        """Check if user has access to a message thread"""
        if not self.user or self.is_anonymous:
            return False
            
        return ThreadParticipant.objects.filter(
            thread_id=thread_id,
            user=self.user,
            is_active=True
        ).exists()
    
    @database_sync_to_async
    def get_thread_info(self, thread_id):
        """Get information about a message thread"""
        try:
            thread = MessageThread.objects.get(id=thread_id)
            participants = thread.thread_participants.select_related('user')
            
            return {
                'id': str(thread.id),
                'subject': thread.subject,
                'thread_type': thread.thread_type,
                'thread_type_display': thread.get_thread_type_display(),
                'is_active': thread.is_active,
                'is_resolved': thread.is_resolved,
                'created_at': self.encode_datetime(thread.created_at),
                'participants': [
                    {
                        'id': str(p.user.id),
                        'name': f"{p.user.first_name} {p.user.last_name}".strip() or p.user.email,
                        'role': p.role,
                        'role_display': p.get_role_display(),
                        'is_active': p.is_active
                    }
                    for p in participants
                ],
                'related_property_id': str(thread.related_property.id) if thread.related_property else None,
                'related_auction_id': str(thread.related_auction.id) if thread.related_auction else None,
                'related_contract_id': str(thread.related_contract.id) if thread.related_contract else None
            }
        except Exception as e:
            logger.error(f"Error getting thread info: {str(e)}")
            return None
    
    @database_sync_to_async
    def get_recent_messages(self, limit=30):
        """Get recent messages for this chat room or thread"""
        try:
            if self.room_name.startswith('thread_'):
                # For private threads
                thread_id = self.room_name.split('_')[1]
                messages = Message.objects.filter(
                    thread_id=thread_id
                ).select_related('sender').order_by('-sent_at')[:limit]
            else:
                # For public chat rooms
                messages = Message.objects.filter(
                    thread__isnull=True,  # No thread = public chat
                    content__startswith=f"ROOM:{self.room_name}:"
                ).select_related('sender').order_by('-sent_at')[:limit]
                
                # For public chats, we store the room name in the message content
                # Format: "ROOM:room_name:actual message"
                
            # Convert to dict and reverse for chronological order
            serialized = [
                {
                    'id': str(message.id),
                    'user_id': str(message.sender.id) if message.sender else None,
                    'username': message.sender.first_name or message.sender.email.split('@')[0] if message.sender else 'Anonymous',
                    'message': message.content.split(':', 2)[2] if self.room_name.startswith('thread_') is False and ':' in message.content else message.content,
                    'sent_at': self.encode_datetime(message.sent_at),
                    'delivered_at': self.encode_datetime(message.delivered_at),
                    'read_at': self.encode_datetime(message.read_at)
                }
                for message in reversed(messages)  # Reverse to get chronological order
            ]
            
            return serialized
        except Exception as e:
            logger.error(f"Error getting recent messages: {str(e)}")
            return []
    
    @database_sync_to_async
    def get_messages_before(self, before_id, limit=20):
        """Get messages before a specific message ID"""
        try:
            if self.room_name.startswith('thread_'):
                # For private threads
                thread_id = self.room_name.split('_')[1]
                
                if before_id:
                    messages = Message.objects.filter(
                        thread_id=thread_id,
                        id__lt=before_id
                    ).select_related('sender').order_by('-sent_at')[:limit]
                else:
                    messages = Message.objects.filter(
                        thread_id=thread_id
                    ).select_related('sender').order_by('-sent_at')[:limit]
            else:
                # For public chat rooms
                if before_id:
                    messages = Message.objects.filter(
                        thread__isnull=True,
                        content__startswith=f"ROOM:{self.room_name}:",
                        id__lt=before_id
                    ).select_related('sender').order_by('-sent_at')[:limit]
                else:
                    messages = Message.objects.filter(
                        thread__isnull=True,
                        content__startswith=f"ROOM:{self.room_name}:"
                    ).select_related('sender').order_by('-sent_at')[:limit]
                
            # Convert to dict and reverse for chronological order
            serialized = [
                {
                    'id': str(message.id),
                    'user_id': str(message.sender.id) if message.sender else None,
                    'username': message.sender.first_name or message.sender.email.split('@')[0] if message.sender else 'Anonymous',
                    'message': message.content.split(':', 2)[2] if self.room_name.startswith('thread_') is False and ':' in message.content else message.content,
                    'sent_at': self.encode_datetime(message.sent_at),
                    'delivered_at': self.encode_datetime(message.delivered_at),
                    'read_at': self.encode_datetime(message.read_at)
                }
                for message in reversed(messages)  # Reverse to get chronological order
            ]
            
            return serialized
        except Exception as e:
            logger.error(f"Error getting messages before {before_id}: {str(e)}")
            return []
    
    @database_sync_to_async
    def save_thread_message(self, thread_id, message_text):
        """Save a message to a private thread"""
        if not self.user or self.is_anonymous:
            return None
            
        try:
            with transaction.atomic():
                # Create message
                message = Message.objects.create(
                    thread_id=thread_id,
                    sender=self.user,
                    subject=None,  # Subject is optional
                    content=message_text,
                    message_type='inquiry',  # Default type
                    sent_at=timezone.now()
                )
                
                # Update thread's last_message_at
                MessageThread.objects.filter(id=thread_id).update(
                    last_message_at=timezone.now()
                )
                
                return str(message.id)
        except Exception as e:
            logger.error(f"Error saving thread message: {str(e)}")
            return None
    
    @database_sync_to_async
    def save_chat_message(self, message_text):
        """Save a message to a public chat room"""
        try:
            with transaction.atomic():
                # For public chats, we store messages without a thread
                # But we prepend the room name to the content
                full_message = f"ROOM:{self.room_name}:{message_text}"
                
                # Create message
                message = Message.objects.create(
                    thread=None,  # No thread = public chat
                    sender=self.user if not self.is_anonymous else None,
                    subject=None,
                    content=full_message,
                    message_type='notification',  # Different type for public chats
                    sent_at=timezone.now()
                )
                
                return str(message.id)
        except Exception as e:
            logger.error(f"Error saving chat message: {str(e)}")
            return None
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark a message as read"""
        if not self.user or self.is_anonymous:
            return False
            
        try:
            # Update the message read status
            message = Message.objects.get(id=message_id)
            
            # Only mark as read if it's not the sender and not already read
            if message.sender != self.user and not message.read_at:
                message.read_at = timezone.now()
                message.save(update_fields=['read_at'])
                
                # Send read receipt to the room
                self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'read_receipt',
                        'message_id': message_id,
                        'user_id': str(self.user.id),
                        'timestamp': timezone.now().isoformat()
                    }
                )
                
                return True
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            
        return False
    
    # Helper methods
    def _validate_room_name(self, room_name):
        """
        Validate room_name to prevent security issues.
        Rules:
        - Must be alphanumeric with underscores, hyphens or dots only
        - Length between 3 and 100 characters
        - No consecutive special characters
        - Cannot start or end with special character
        - For thread rooms, allow "thread_<uuid>" format
        """
        # Check for thread format
        if room_name and room_name.startswith('thread_'):
            parts = room_name.split('_')
            if len(parts) != 2:
                return False
                
            # Validate thread ID part
            thread_id = parts[1]
            import uuid
            try:
                uuid.UUID(thread_id)
                return True
            except ValueError:
                return False
        
        # Basic length check
        if not room_name or not (3 <= len(room_name) <= 100):
            return False
            
        # Check for consecutive special characters
        if '__' in room_name or '--' in room_name or '..' in room_name:
            return False
            
        # Check start/end characters
        if room_name[0] in '_-.' or room_name[-1] in '_-.':
            return False
            
        # Additional pattern validation
        pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_\-\.]*[a-zA-Z0-9]$')
        if not pattern.match(room_name) and len(room_name) > 1:
            return False
            
        return True