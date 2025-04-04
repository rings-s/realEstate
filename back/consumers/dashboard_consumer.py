# consumers/dashboard_consumer.py

import json
from channels.db import database_sync_to_async
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.core.exceptions import ObjectDoesNotExist

from .base_consumer import BaseConsumer
from base.models import (
    Property, Auction, Bid, Contract, Payment, 
    Transaction, Notification, MessageThread
)

class DashboardConsumer(BaseConsumer):
    """
    WebSocket consumer for real-time dashboard updates.
    Provides property metrics, auction activity, contract status,
    and financial transaction data.
    """
    group_prefix = 'dashboard'
    
    async def authenticate(self):
        """Ensure the user is authenticated and authorized for this dashboard"""
        user = self.scope.get('user')
        requested_user_id = self.params.get('user_id')
        
        if not user or not user.is_authenticated:
            return False
            
        # Users can only access their own dashboard unless they're staff/admin
        if str(user.id) != requested_user_id and not user.is_staff:
            return False
            
        return True
    
    async def get_initial_data(self):
        """Get initial dashboard data"""
        try:
            dashboard_data = await self.get_dashboard_data()
            return {
                'type': 'dashboard_data',
                'data': dashboard_data
            }
        except Exception as e:
            self.logger.error(f"Error getting initial dashboard data: {str(e)}")
            return {
                'type': 'error',
                'message': 'Failed to load dashboard data',
                'details': str(e)
            }
    
    async def process_message(self, data):
        """Process messages from the client"""
        action = data.get('action')
        
        if action == 'refresh_dashboard':
            # User requested a refresh of dashboard data
            dashboard_data = await self.get_dashboard_data()
            await self.send(text_data=json.dumps({
                'type': 'dashboard_data',
                'data': dashboard_data
            }))
            
        elif action == 'get_section':
            # Get specific dashboard section data
            section = data.get('section')
            if section:
                section_data = await self.get_section_data(section)
                await self.send(text_data=json.dumps({
                    'type': 'section_data',
                    'section': section,
                    'data': section_data
                }))
            else:
                await self.send_error('Invalid section specified')
                
        elif action == 'get_chart_data':
            # Get data for a specific chart
            chart_type = data.get('chart_type')
            if chart_type:
                chart_data = await self.get_chart_data(chart_type, data.get('params', {}))
                await self.send(text_data=json.dumps({
                    'type': 'chart_data',
                    'chart_type': chart_type,
                    'data': chart_data
                }))
            else:
                await self.send_error('Invalid chart type specified')
    
    # Event handlers for group messages
    async def dashboard_update(self, event):
        """Handle dashboard update event"""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'update_type': event['update_type'],
            'data': event['data']
        }))
    
    async def auction_update(self, event):
        """Handle auction update event that affects dashboard"""
        await self.send(text_data=json.dumps({
            'type': 'auction_update',
            'auction_id': event['auction_id'],
            'update_type': event['update_type'],
            'data': event['data']
        }))
    
    async def bid_update(self, event):
        """Handle bid update event that affects dashboard"""
        await self.send(text_data=json.dumps({
            'type': 'bid_update',
            'auction_id': event['auction_id'],
            'update_type': event['update_type'],
            'data': event['data']
        }))
    
    async def transaction_update(self, event):
        """Handle transaction update event"""
        await self.send(text_data=json.dumps({
            'type': 'transaction_update',
            'transaction_id': event['transaction_id'],
            'update_type': event['update_type'],
            'data': event['data']
        }))
    
    async def notification_event(self, event):
        """Handle notification event that affects dashboard"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    # Database access methods
    @database_sync_to_async
    def get_dashboard_data(self):
        """Get complete dashboard data for the user"""
        try:
            user_id = self.params.get('user_id')
            user = self.scope['user']
            
            # Properties statistics
            owned_properties = Property.objects.filter(owner=user)
            active_properties = owned_properties.filter(status='active').count()
            total_properties = owned_properties.count()
            
            # Auctions statistics
            user_auctions = Auction.objects.filter(created_by=user)
            active_auctions = user_auctions.filter(status='active').count()
            total_auctions = user_auctions.count()
            
            # Bids statistics
            user_bids = Bid.objects.filter(bidder=user)
            active_bids = user_bids.filter(auction__status='active').count()
            won_bids = user_bids.filter(status='winning').count()
            
            # Contracts statistics
            buyer_contracts = Contract.objects.filter(buyer=user)
            seller_contracts = Contract.objects.filter(seller=user)
            active_contracts = buyer_contracts.filter(status='active').count() + seller_contracts.filter(status='active').count()
            completed_contracts = buyer_contracts.filter(status='completed').count() + seller_contracts.filter(status='completed').count()
            
            # Financial statistics
            total_purchase_value = buyer_contracts.filter(status='completed').aggregate(Sum('contract_amount'))['contract_amount__sum'] or 0
            total_sales_value = seller_contracts.filter(status='completed').aggregate(Sum('contract_amount'))['contract_amount__sum'] or 0
            
            # Recent activity data
            recent_properties = self._serialize_properties(
                owned_properties.order_by('-created_at')[:5]
            )
            
            recent_auctions = self._serialize_auctions(
                user_auctions.order_by('-created_at')[:5]
            )
            
            recent_bids = self._serialize_bids(
                user_bids.select_related('auction', 'auction__related_property').order_by('-created_at')[:5]
            )
            
            recent_contracts = self._serialize_contracts(
                list(buyer_contracts.order_by('-created_at')[:3]) + 
                list(seller_contracts.order_by('-created_at')[:3])
            )
            
            # Get unread notifications
            recent_notifications = self._serialize_notifications(
                Notification.objects.filter(
                    recipient=user,
                    is_read=False
                ).order_by('-created_at')[:5]
            )
            
            # Get unread messages
            unread_messages_count = MessageThread.objects.filter(
                participants=user
            ).annotate(
                unread=Count('messages', filter=Q(messages__read_at=None) & ~Q(messages__sender=user))
            ).filter(unread__gt=0).count()
            
            # Compile all dashboard data
            dashboard_data = {
                'statistics': {
                    'properties': {
                        'total': total_properties,
                        'active': active_properties
                    },
                    'auctions': {
                        'total': total_auctions,
                        'active': active_auctions
                    },
                    'bids': {
                        'total': user_bids.count(),
                        'active': active_bids,
                        'won': won_bids
                    },
                    'contracts': {
                        'total': buyer_contracts.count() + seller_contracts.count(),
                        'active': active_contracts,
                        'completed': completed_contracts
                    },
                    'financials': {
                        'total_purchases': self.format_decimal(total_purchase_value),
                        'total_sales': self.format_decimal(total_sales_value),
                        'net_position': self.format_decimal(total_sales_value - total_purchase_value)
                    },
                    'messages': {
                        'unread': unread_messages_count
                    },
                    'notifications': {
                        'unread': Notification.objects.filter(recipient=user, is_read=False).count()
                    }
                },
                'recent_activity': {
                    'properties': recent_properties,
                    'auctions': recent_auctions,
                    'bids': recent_bids,
                    'contracts': recent_contracts,
                    'notifications': recent_notifications
                },
                'timestamp': self.encode_datetime(timezone.now())
            }
            
            return dashboard_data
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {str(e)}")
            return {
                'error': f'Failed to load dashboard data: {str(e)}',
                'timestamp': self.encode_datetime(timezone.now())
            }
    
    @database_sync_to_async
    def get_section_data(self, section):
        """Get data for a specific dashboard section"""
        try:
            user = self.scope['user']
            
            if section == 'properties':
                # Get property statistics and recent properties
                owned_properties = Property.objects.filter(owner=user)
                return {
                    'statistics': {
                        'total': owned_properties.count(),
                        'active': owned_properties.filter(status='active').count(),
                        'draft': owned_properties.filter(status='draft').count(),
                        'sold': owned_properties.filter(status='sold').count(),
                        'value': self.format_decimal(owned_properties.aggregate(Sum('estimated_value'))['estimated_value__sum'] or 0)
                    },
                    'recent': self._serialize_properties(
                        owned_properties.order_by('-created_at')[:10]
                    )
                }
                
            elif section == 'auctions':
                # Get auction statistics and recent auctions
                user_auctions = Auction.objects.filter(created_by=user)
                return {
                    'statistics': {
                        'total': user_auctions.count(),
                        'active': user_auctions.filter(status='active').count(),
                        'completed': user_auctions.filter(status__in=['closed', 'sold']).count(),
                        'upcoming': user_auctions.filter(
                            status='pending', 
                            start_date__gt=timezone.now()
                        ).count()
                    },
                    'recent': self._serialize_auctions(
                        user_auctions.order_by('-created_at')[:10]
                    )
                }
                
            elif section == 'bids':
                # Get bid statistics and recent bids
                user_bids = Bid.objects.filter(bidder=user)
                return {
                    'statistics': {
                        'total': user_bids.count(),
                        'active': user_bids.filter(auction__status='active').count(),
                        'won': user_bids.filter(status='winning').count(),
                        'outbid': user_bids.filter(status='outbid').count(),
                        'total_value': self.format_decimal(user_bids.aggregate(Sum('bid_amount'))['bid_amount__sum'] or 0)
                    },
                    'recent': self._serialize_bids(
                        user_bids.select_related('auction', 'auction__related_property').order_by('-created_at')[:10]
                    )
                }
                
            elif section == 'contracts':
                # Get contract statistics and recent contracts
                buyer_contracts = Contract.objects.filter(buyer=user)
                seller_contracts = Contract.objects.filter(seller=user)
                
                return {
                    'statistics': {
                        'total': buyer_contracts.count() + seller_contracts.count(),
                        'as_buyer': buyer_contracts.count(),
                        'as_seller': seller_contracts.count(),
                        'active': buyer_contracts.filter(status='active').count() + seller_contracts.filter(status='active').count(),
                        'completed': buyer_contracts.filter(status='completed').count() + seller_contracts.filter(status='completed').count(),
                        'pending': buyer_contracts.filter(status__in=['pending_buyer', 'pending_seller', 'pending_payment']).count() + 
                                  seller_contracts.filter(status__in=['pending_buyer', 'pending_seller', 'pending_payment']).count(),
                        'purchase_value': self.format_decimal(buyer_contracts.filter(status='completed').aggregate(Sum('contract_amount'))['contract_amount__sum'] or 0),
                        'sales_value': self.format_decimal(seller_contracts.filter(status='completed').aggregate(Sum('contract_amount'))['contract_amount__sum'] or 0)
                    },
                    'recent': self._serialize_contracts(
                        list(buyer_contracts.order_by('-created_at')[:5]) + 
                        list(seller_contracts.order_by('-created_at')[:5])
                    )
                }
                
            elif section == 'financials':
                # Get financial statistics
                buyer_contracts = Contract.objects.filter(buyer=user)
                seller_contracts = Contract.objects.filter(seller=user)
                
                # Payments made
                payments_made = Payment.objects.filter(payer=user)
                
                # Payments received
                payments_received = Payment.objects.filter(payee=user)
                
                # Transactions
                transactions_out = Transaction.objects.filter(from_user=user)
                transactions_in = Transaction.objects.filter(to_user=user)
                
                return {
                    'purchase_value': self.format_decimal(buyer_contracts.filter(status='completed').aggregate(Sum('contract_amount'))['contract_amount__sum'] or 0),
                    'sales_value': self.format_decimal(seller_contracts.filter(status='completed').aggregate(Sum('contract_amount'))['contract_amount__sum'] or 0),
                    'payments_made': self.format_decimal(payments_made.aggregate(Sum('amount'))['amount__sum'] or 0),
                    'payments_received': self.format_decimal(payments_received.aggregate(Sum('amount'))['amount__sum'] or 0),
                    'transactions_out': self.format_decimal(transactions_out.aggregate(Sum('amount'))['amount__sum'] or 0),
                    'transactions_in': self.format_decimal(transactions_in.aggregate(Sum('amount'))['amount__sum'] or 0),
                    'net_position': self.format_decimal(
                        (seller_contracts.filter(status='completed').aggregate(Sum('contract_amount'))['contract_amount__sum'] or 0) +
                        (payments_received.aggregate(Sum('amount'))['amount__sum'] or 0) +
                        (transactions_in.aggregate(Sum('amount'))['amount__sum'] or 0) -
                        (buyer_contracts.filter(status='completed').aggregate(Sum('contract_amount'))['contract_amount__sum'] or 0) -
                        (payments_made.aggregate(Sum('amount'))['amount__sum'] or 0) -
                        (transactions_out.aggregate(Sum('amount'))['amount__sum'] or 0)
                    )
                }
                
            elif section == 'notifications':
                # Get notifications
                notifications = Notification.objects.filter(recipient=user)
                return {
                    'unread': notifications.filter(is_read=False).count(),
                    'total': notifications.count(),
                    'recent': self._serialize_notifications(
                        notifications.order_by('-created_at')[:20]
                    )
                }
                
            else:
                return {
                    'error': f'Unknown section: {section}'
                }
                
        except Exception as e:
            self.logger.error(f"Error getting section data: {str(e)}")
            return {'error': f'Failed to load section data: {str(e)}'}
    
    @database_sync_to_async
    def get_chart_data(self, chart_type, params=None):
        """Get data for a specific chart"""
        try:
            if params is None:
                params = {}
                
            user = self.scope['user']
            
            if chart_type == 'property_value_history':
                # Get property value history (using estimated_value)
                properties = Property.objects.filter(owner=user)
                return {
                    'labels': [p.created_at.strftime('%b %Y') for p in properties],
                    'datasets': [{
                        'label': 'Property Value (SAR)',
                        'data': [self.format_decimal(p.estimated_value) for p in properties]
                    }]
                }
                
            elif chart_type == 'auction_activity':
                # Get auction activity over time
                auctions = Auction.objects.filter(created_by=user)
                return {
                    'labels': [a.created_at.strftime('%b %Y') for a in auctions],
                    'datasets': [{
                        'label': 'Auctions',
                        'data': [1 for _ in auctions]  # Count of 1 per auction
                    }]
                }
                
            elif chart_type == 'bid_history':
                # Get bid history
                bids = Bid.objects.filter(bidder=user).order_by('created_at')
                return {
                    'labels': [b.created_at.strftime('%d %b %Y') for b in bids],
                    'datasets': [{
                        'label': 'Bid Amount (SAR)',
                        'data': [self.format_decimal(b.bid_amount) for b in bids]
                    }]
                }
                
            elif chart_type == 'contract_value':
                # Get contract values over time
                buyer_contracts = Contract.objects.filter(buyer=user).order_by('created_at')
                seller_contracts = Contract.objects.filter(seller=user).order_by('created_at')
                
                return {
                    'labels': [
                        c.created_at.strftime('%b %Y') 
                        for c in sorted(list(buyer_contracts) + list(seller_contracts), key=lambda x: x.created_at)
                    ],
                    'datasets': [
                        {
                            'label': 'Purchases (SAR)',
                            'data': [self.format_decimal(c.contract_amount) if c in buyer_contracts else 0 
                                    for c in sorted(list(buyer_contracts) + list(seller_contracts), key=lambda x: x.created_at)]
                        },
                        {
                            'label': 'Sales (SAR)',
                            'data': [self.format_decimal(c.contract_amount) if c in seller_contracts else 0 
                                    for c in sorted(list(buyer_contracts) + list(seller_contracts), key=lambda x: x.created_at)]
                        }
                    ]
                }
                
            else:
                return {
                    'error': f'Unknown chart type: {chart_type}'
                }
                
        except Exception as e:
            self.logger.error(f"Error getting chart data: {str(e)}")
            return {'error': f'Failed to load chart data: {str(e)}'}
    
    # Helper methods for serializing models
    def _serialize_properties(self, properties):
        """Serialize property objects for dashboard display"""
        result = []
        for prop in properties:
            result.append({
                'id': str(prop.id),
                'property_number': prop.property_number,
                'title': prop.title,
                'property_type': prop.property_type,
                'property_type_display': prop.get_property_type_display(),
                'city': prop.city,
                'district': prop.district,
                'status': prop.status,
                'status_display': prop.get_status_display(),
                'estimated_value': self.format_decimal(prop.estimated_value),
                'area': self.format_decimal(prop.area),
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'has_auction': prop.has_auction,
                'main_image_url': prop.main_image_url,
                'is_featured': prop.is_featured,
                'is_published': prop.is_published,
                'created_at': self.encode_datetime(prop.created_at),
                'updated_at': self.encode_datetime(prop.updated_at)
            })
        return result
    
    def _serialize_auctions(self, auctions):
        """Serialize auction objects for dashboard display"""
        result = []
        for auction in auctions:
            result.append({
                'id': str(auction.id),
                'title': auction.title,
                'uuid': str(auction.uuid),
                'slug': auction.slug,
                'property_title': auction.related_property.title if auction.related_property else None,
                'property_type': auction.related_property.property_type if auction.related_property else None,
                'property_type_display': auction.related_property.get_property_type_display() if auction.related_property else None,
                'auction_type': auction.auction_type,
                'auction_type_display': auction.get_auction_type_display(),
                'status': auction.status,
                'status_display': auction.get_status_display(),
                'start_date': self.encode_datetime(auction.start_date),
                'end_date': self.encode_datetime(auction.end_date),
                'starting_price': self.format_decimal(auction.starting_price),
                'current_bid': self.format_decimal(auction.current_bid),
                'min_bid_increment': self.format_decimal(auction.min_bid_increment),
                'reserve_price': self.format_decimal(auction.reserve_price),
                'winning_bid': self.format_decimal(auction.winning_bid),
                'is_featured': auction.is_featured,
                'is_published': auction.is_published,
                'featured_image_url': auction.featured_image_url,
                'bid_count': auction.bid_count,
                'time_remaining': auction.time_remaining,
                'created_at': self.encode_datetime(auction.created_at),
                'updated_at': self.encode_datetime(auction.updated_at)
            })
        return result
    
    def _serialize_bids(self, bids):
        """Serialize bid objects for dashboard display"""
        result = []
        for bid in bids:
            result.append({
                'id': str(bid.id),
                'auction': str(bid.auction.id),
                'auction_details': {
                    'title': bid.auction.title,
                    'status': bid.auction.status,
                    'status_display': bid.auction.get_status_display(),
                    'end_date': self.encode_datetime(bid.auction.end_date),
                    'property_title': bid.auction.related_property.title if hasattr(bid.auction, 'related_property') else None,
                },
                'bid_amount': self.format_decimal(bid.bid_amount),
                'max_bid_amount': self.format_decimal(bid.max_bid_amount) if hasattr(bid, 'max_bid_amount') else None,
                'is_auto_bid': bid.is_auto_bid,
                'status': bid.status,
                'status_display': bid.get_status_display(),
                'bid_time': self.encode_datetime(bid.bid_time),
                'created_at': self.encode_datetime(bid.created_at),
                'updated_at': self.encode_datetime(bid.updated_at)
            })
        return result
    
    def _serialize_contracts(self, contracts):
        """Serialize contract objects for dashboard display"""
        result = []
        for contract in contracts:
            result.append({
                'id': str(contract.id),
                'contract_number': contract.contract_number,
                'title': contract.title,
                'property': {
                    'id': str(contract.related_property.id),
                    'title': contract.related_property.title,
                    'property_type': contract.related_property.property_type,
                    'property_type_display': contract.related_property.get_property_type_display(),
                } if contract.related_property else None,
                'auction': {
                    'id': str(contract.auction.id),
                    'title': contract.auction.title,
                } if contract.auction else None,
                'buyer': {
                    'id': str(contract.buyer.id),
                    'name': f"{contract.buyer.first_name} {contract.buyer.last_name}".strip(),
                } if contract.buyer else None,
                'seller': {
                    'id': str(contract.seller.id),
                    'name': f"{contract.seller.first_name} {contract.seller.last_name}".strip(),
                } if contract.seller else None,
                'status': contract.status,
                'status_display': contract.get_status_display(),
                'contract_date': self.encode_datetime(contract.contract_date),
                'effective_date': self.encode_datetime(contract.effective_date),
                'expiry_date': self.encode_datetime(contract.expiry_date),
                'contract_amount': self.format_decimal(contract.contract_amount),
                'commission_amount': self.format_decimal(contract.commission_amount),
                'tax_amount': self.format_decimal(contract.tax_amount),
                'total_amount': self.format_decimal(contract.total_amount),
                'payment_method': contract.payment_method,
                'payment_method_display': contract.get_payment_method_display(),
                'is_fully_signed': contract.is_fully_signed,
                'created_at': self.encode_datetime(contract.created_at),
                'updated_at': self.encode_datetime(contract.updated_at)
            })
        return result
    
    def _serialize_notifications(self, notifications):
        """Serialize notification objects for dashboard display"""
        result = []
        for notification in notifications:
            result.append({
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
            })
        return result