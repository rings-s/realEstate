"""
Base app utilities for Real Estate Auction Platform.

This module provides utility functions used throughout the base app,
including response formatting, validation, query optimization, and more.
"""

import logging
import uuid
import json
import base64
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Count, Sum, Avg, F, Value, QuerySet
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response

# Configure logger
logger = logging.getLogger(__name__)
User = get_user_model()

# ============================================================================
# Response Formatting
# ============================================================================

def create_response(
    data: Any = None, 
    message: str = None,
    error: str = None,
    error_code: str = None,
    status_code: int = status.HTTP_200_OK
) -> Response:
    """
    Create a standardized API response.
    
    Args:
        data: Response data (optional)
        message: Success message (optional)
        error: Error message (optional)
        error_code: Error code for client (optional)
        status_code: HTTP status code (default: 200)
        
    Returns:
        Response: Formatted DRF response object
    """
    response_data = {"status": "success" if not error else "error"}
    
    if message:
        response_data["message"] = message
    
    if data is not None:
        response_data["data"] = data
    
    if error:
        response_data["error"] = error
        
    if error_code:
        response_data["error_code"] = error_code
    
    return Response(response_data, status=status_code)


def paginate_response(
    queryset: QuerySet,
    request,
    serializer_class,
    extra_data: Dict = None
) -> Response:
    """
    Create a paginated response with standardized format.
    
    Args:
        queryset: Django queryset to paginate
        request: The request object from the view
        serializer_class: Serializer to use for the queryset
        extra_data: Additional data to include in response
        
    Returns:
        Response: Paginated DRF response
    """
    paginator = request.parser_context['view'].pagination_class()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = serializer_class(page, many=True, context={'request': request})
        response = paginator.get_paginated_response(serializer.data)
        
        # Add extra data if provided
        if extra_data:
            response_data = response.data
            for key, value in extra_data.items():
                response_data[key] = value
            return Response(response_data)
        
        return response
    
    serializer = serializer_class(queryset, many=True, context={'request': request})
    return Response(serializer.data)


# ============================================================================
# Validation Utilities
# ============================================================================

def validate_status_transition(
    original_status: str, 
    new_status: str, 
    allowed_transitions: Dict[str, List[str]]
) -> bool:
    """
    Validate if a status transition is allowed.
    
    Args:
        original_status: Current status
        new_status: Proposed new status
        allowed_transitions: Dictionary of allowed transitions
        
    Returns:
        bool: True if transition is valid, False otherwise
        
    Raises:
        ValidationError: If transition is not allowed
    """
    if original_status == new_status:
        return True
        
    if original_status not in allowed_transitions:
        raise ValidationError(_(f"Invalid original status: {original_status}"))
        
    if new_status not in allowed_transitions[original_status]:
        allowed = ", ".join(allowed_transitions[original_status])
        raise ValidationError(
            _(f"Cannot transition from '{original_status}' to '{new_status}'. "
              f"Allowed transitions: {allowed}")
        )
        
    return True


def validate_date_range(start_date: datetime, end_date: datetime, min_duration: timedelta = None) -> bool:
    """
    Validate a date range (e.g., for auctions).
    
    Args:
        start_date: Start date/time
        end_date: End date/time
        min_duration: Minimum required duration (optional)
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If date range is invalid
    """
    now = timezone.now()
    
    if start_date < now:
        raise ValidationError(_("Start date cannot be in the past"))
        
    if end_date <= start_date:
        raise ValidationError(_("End date must be after start date"))
        
    if min_duration and (end_date - start_date) < min_duration:
        hours = min_duration.total_seconds() / 3600
        raise ValidationError(_(f"Duration must be at least {hours} hours"))
        
    return True


def validate_bid_amount(
    amount: Decimal, 
    highest_bid: Decimal, 
    min_increment: Decimal
) -> bool:
    """
    Validate if a bid amount is valid.
    
    Args:
        amount: Bid amount to validate
        highest_bid: Current highest bid
        min_increment: Minimum bid increment
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If bid amount is invalid
    """
    min_valid_bid = highest_bid + min_increment
    
    if amount < min_valid_bid:
        raise ValidationError(
            _(f"Bid must be at least {min_valid_bid} (current highest bid plus minimum increment)")
        )
        
    return True


def validate_document(file_obj, max_size_mb: int = 10, allowed_types: List[str] = None) -> bool:
    """
    Validate a document file upload.
    
    Args:
        file_obj: The file object to validate
        max_size_mb: Maximum file size in MB
        allowed_types: List of allowed MIME types
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If file is invalid
    """
    if not file_obj:
        raise ValidationError(_("No file provided"))
        
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_obj.size > max_size_bytes:
        raise ValidationError(_(f"File size exceeds the limit of {max_size_mb}MB"))
    
    # Check file type if specified
    if allowed_types:
        content_type = file_obj.content_type
        if content_type not in allowed_types:
            allowed = ", ".join(allowed_types)
            raise ValidationError(_(f"Invalid file type. Allowed types: {allowed}"))
    
    return True


# ============================================================================
# Query Optimization
# ============================================================================

def optimize_property_query(queryset: QuerySet) -> QuerySet:
    """
    Optimize a property queryset with select_related and prefetch_related.
    
    Args:
        queryset: Base property queryset
        
    Returns:
        QuerySet: Optimized queryset
    """
    return queryset.select_related(
        'owner', 
        'appraiser'
    ).prefetch_related(
        'auctions', 
        'documents', 
        'property_views'
    )


def optimize_auction_query(queryset: QuerySet) -> QuerySet:
    """
    Optimize an auction queryset with select_related and prefetch_related.
    
    Args:
        queryset: Base auction queryset
        
    Returns:
        QuerySet: Optimized queryset
    """
    return queryset.select_related(
        'related_property', 
        'created_by', 
        'auctioneer'
    ).prefetch_related(
        'bids', 
        'documents', 
        'invited_bidders', 
        'property_views'
    )


def optimize_bid_query(queryset: QuerySet) -> QuerySet:
    """
    Optimize a bid queryset with select_related.
    
    Args:
        queryset: Base bid queryset
        
    Returns:
        QuerySet: Optimized queryset
    """
    return queryset.select_related(
        'auction', 
        'bidder', 
        'auction__related_property'
    )


def optimize_contract_query(queryset: QuerySet) -> QuerySet:
    """
    Optimize a contract queryset with select_related and prefetch_related.
    
    Args:
        queryset: Base contract queryset
        
    Returns:
        QuerySet: Optimized queryset
    """
    return queryset.select_related(
        'buyer', 
        'seller', 
        'agent', 
        'related_property',
        'auction'
    ).prefetch_related(
        'documents', 
        'payments'
    )


def optimize_document_query(queryset: QuerySet) -> QuerySet:
    """
    Optimize a document queryset with select_related.
    
    Args:
        queryset: Base document queryset
        
    Returns:
        QuerySet: Optimized queryset
    """
    return queryset.select_related(
        'uploaded_by', 
        'verified_by', 
        'related_property', 
        'auction', 
        'contract'
    )


def optimize_payment_query(queryset: QuerySet) -> QuerySet:
    """
    Optimize a payment queryset with select_related.
    
    Args:
        queryset: Base payment queryset
        
    Returns:
        QuerySet: Optimized queryset
    """
    return queryset.select_related(
        'payer', 
        'payee', 
        'contract', 
        'confirmed_by'
    )


def optimize_transaction_query(queryset: QuerySet) -> QuerySet:
    """
    Optimize a transaction queryset with select_related.
    
    Args:
        queryset: Base transaction queryset
        
    Returns:
        QuerySet: Optimized queryset
    """
    return queryset.select_related(
        'from_user', 
        'to_user', 
        'payment', 
        'contract', 
        'auction', 
        'processed_by'
    )


def optimize_notification_query(queryset: QuerySet) -> QuerySet:
    """
    Optimize a notification queryset with select_related.
    
    Args:
        queryset: Base notification queryset
        
    Returns:
        QuerySet: Optimized queryset
    """
    return queryset.select_related(
        'recipient', 
        'related_property',
        'related_auction',
        'related_bid',
        'related_contract',
        'related_payment',
        'related_message'
    )


# ============================================================================
# Slug and Unique ID Generation
# ============================================================================

def generate_unique_slug(
    instance, 
    title_field: str = 'title', 
    slug_field: str = 'slug'
) -> str:
    """
    Generate a unique slug for a model instance.
    
    Args:
        instance: Model instance
        title_field: Name of field to generate slug from
        slug_field: Name of slug field
        
    Returns:
        str: Unique slug
    """
    max_length = instance._meta.get_field(slug_field).max_length
    title = getattr(instance, title_field)
    slug = slugify(title)
    
    if len(slug) > max_length:
        slug = slug[:max_length]
        
    model = instance.__class__
    
    # Check if slug exists
    qs = model.objects.filter(**{slug_field: slug})
    
    # Exclude current instance if updating
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
        
    # If slug exists, add a random suffix
    if qs.exists():
        slug_suffix = str(uuid.uuid4())[:8]
        slug = f"{slug[:(max_length-9)]}-{slug_suffix}"
        
    return slug


def generate_reference_number(prefix: str, model_class, ref_field: str) -> str:
    """
    Generate a unique reference number for models like contracts, payments, etc.
    
    Args:
        prefix: Prefix for the reference number (e.g., 'CON', 'PAY')
        model_class: Model class to check uniqueness against
        ref_field: Field name to check uniqueness
        
    Returns:
        str: Unique reference number
    """
    # Format: PREFIX-YYYYMMDD-XXXX (X = random alphanumeric)
    date_part = datetime.now().strftime('%Y%m%d')
    
    # Try to generate a unique reference number
    for _ in range(10):  # Try 10 times max
        random_part = ''.join([str(uuid.uuid4().hex)[:6].upper()])
        reference = f"{prefix}-{date_part}-{random_part}"
        
        # Check if reference exists
        exists = model_class.objects.filter(**{ref_field: reference}).exists()
        if not exists:
            return reference
            
    # Fallback to timestamp if all attempts fail
    timestamp = int(datetime.now().timestamp())
    return f"{prefix}-{date_part}-{timestamp}"


# ============================================================================
# File Handling
# ============================================================================

def handle_uploaded_file(
    file_obj, 
    directory: str = 'uploads', 
    allowed_types: List[str] = None, 
    max_size_mb: int = 10
) -> str:
    """
    Handle an uploaded file and return its storage path.
    
    Args:
        file_obj: Uploaded file
        directory: Target directory in storage
        allowed_types: List of allowed MIME types
        max_size_mb: Maximum file size in MB
        
    Returns:
        str: File storage path
        
    Raises:
        ValidationError: If file validation fails
    """
    # Validate file
    validate_document(file_obj, max_size_mb, allowed_types)
    
    # Generate a unique filename
    original_name = file_obj.name
    file_ext = original_name.split('.')[-1].lower() if '.' in original_name else ''
    unique_name = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else f"{uuid.uuid4().hex}"
    
    # Construct storage path
    storage_path = f"{directory}/{datetime.now().strftime('%Y/%m/%d')}/{unique_name}"
    
    # Save file
    default_storage.save(storage_path, ContentFile(file_obj.read()))
    
    return storage_path


def create_document_from_file(
    file_obj, 
    uploaded_by, 
    document_type: str, 
    title: str = None, 
    description: str = None, 
    **related_fields
) -> 'Document':
    """
    Create a Document instance from an uploaded file.
    
    Args:
        file_obj: Uploaded file
        uploaded_by: User who uploaded the file
        document_type: Type of document (e.g., 'contract', 'inspection')
        title: Document title (optional)
        description: Document description (optional)
        **related_fields: Related model fields (e.g., related_property=property_obj)
        
    Returns:
        Document: The created Document instance
    """
    from .models import Document  # Import here to avoid circular imports
    
    # Handle file storage
    file_path = handle_uploaded_file(
        file_obj, 
        directory=f'documents/{document_type.lower()}',
        allowed_types=['application/pdf', 'image/jpeg', 'image/png', 'application/msword', 
                       'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        max_size_mb=20
    )
    
    # Create document
    document = Document(
        title=title or file_obj.name,
        description=description or f"{document_type} document",
        document_type=document_type,
        file=file_path,
        uploaded_by=uploaded_by,
        **related_fields
    )
    
    document.save()
    return document


# ============================================================================
# Notification Utilities 
# ============================================================================

def create_notification(
    recipient, 
    notification_type: str, 
    title: str, 
    content: str, 
    channel: str = 'app',
    **related_objects
) -> 'Notification':
    """
    Create a notification for a user.
    
    Args:
        recipient: User to notify
        notification_type: Type of notification
        title: Notification title
        content: Notification content
        channel: Notification channel (app, email, sms)
        **related_objects: Related model objects
        
    Returns:
        Notification: The created Notification instance
    """
    from .models import Notification  # Import here to avoid circular imports
    
    notification = Notification(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        content=content,
        channel=channel,
        **related_objects
    )
    
    notification.save()
    return notification


def notify_auction_event(auction, event_type: str, **additional_context) -> List['Notification']:
    """
    Send notifications for auction events.
    
    Args:
        auction: The auction instance
        event_type: Event type (e.g., 'new_bid', 'auction_ended')
        **additional_context: Additional context for the notification
        
    Returns:
        List[Notification]: Created notifications
    """
    from .models import Notification  # Import here to avoid circular imports
    
    notifications = []
    
    # Define notification details based on event type
    event_details = {
        'new_bid': {
            'title': _("New bid placed"),
            'content': _("A new bid has been placed on {auction_title}").format(
                auction_title=auction.title
            ),
            'icon': 'money',
            'color': 'info'
        },
        'auction_ended': {
            'title': _("Auction ended"),
            'content': _("The auction for {auction_title} has ended").format(
                auction_title=auction.title
            ),
            'icon': 'clock',
            'color': 'warning'
        },
        'auction_extended': {
            'title': _("Auction extended"),
            'content': _("The auction for {auction_title} has been extended").format(
                auction_title=auction.title
            ),
            'icon': 'clock',
            'color': 'info'
        },
        'winning_bid': {
            'title': _("Winning bid"),
            'content': _("Your bid on {auction_title} has been selected as the winning bid").format(
                auction_title=auction.title
            ),
            'icon': 'trophy',
            'color': 'success'
        },
    }
    
    if event_type not in event_details:
        raise ValueError(f"Unknown event type: {event_type}")
        
    details = event_details[event_type]
    
    # Override content if provided
    if 'content' in additional_context:
        details['content'] = additional_context.pop('content')
        
    # Recipients depend on event type
    recipients = []
    
    if event_type == 'new_bid':
        # Notify property owner and auction creator
        recipients.append(auction.related_property.owner)
        if auction.created_by != auction.related_property.owner:
            recipients.append(auction.created_by)
        
        # If auctioneer is different, notify them too
        if auction.auctioneer and auction.auctioneer not in recipients:
            recipients.append(auction.auctioneer)
            
    elif event_type == 'winning_bid':
        # Only notify the winning bidder
        if 'winning_bid' in additional_context:
            recipients.append(additional_context['winning_bid'].bidder)
            
    elif event_type in ['auction_ended', 'auction_extended']:
        # Notify all bidders, property owner, and auction creator
        bidders = auction.bids.values_list('bidder', flat=True).distinct()
        for bidder_id in bidders:
            try:
                bidder = User.objects.get(id=bidder_id)
                recipients.append(bidder)
            except User.DoesNotExist:
                continue
                
        # Add property owner and auction creator if not already included
        if auction.related_property.owner not in recipients:
            recipients.append(auction.related_property.owner)
            
        if auction.created_by not in recipients:
            recipients.append(auction.created_by)
            
    # Create notifications for all recipients
    for recipient in recipients:
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=event_type,
            title=details['title'],
            content=details['content'],
            related_auction=auction,
            related_property=auction.related_property,
            icon=details.get('icon'),
            color=details.get('color'),
            channel='app',
            action_url=f'/auctions/{auction.id}',
            **additional_context
        )
        notifications.append(notification)
        
    return notifications


# ============================================================================
# Model Helpers
# ============================================================================

def get_auction_status(auction) -> Tuple[str, bool]:
    """
    Get the current status and active state of an auction.
    
    Args:
        auction: Auction instance
        
    Returns:
        Tuple[str, bool]: Status and is_active flag
    """
    now = timezone.now()
    
    if not auction.is_published:
        return 'unpublished', False
        
    if auction.status == 'draft':
        return 'draft', False
        
    if auction.status == 'cancelled':
        return 'cancelled', False
        
    if auction.status == 'closed':
        return 'closed', False
        
    if now < auction.start_date:
        return 'scheduled', False
        
    if now > auction.end_date:
        # Auction has ended but status not yet updated
        return 'ended', False
        
    # Auction is active
    time_left = (auction.end_date - now).total_seconds()
    
    if time_left < 300:  # Less than 5 minutes left
        return 'ending_soon', True
        
    return 'active', True


def calculate_time_remaining(end_date: datetime) -> int:
    """
    Calculate time remaining in seconds.
    
    Args:
        end_date: End date/time
        
    Returns:
        int: Seconds remaining (0 if ended)
    """
    now = timezone.now()
    
    if now > end_date:
        return 0
        
    return int((end_date - now).total_seconds())


def extend_auction_end_time(auction, minutes: int = 30) -> datetime:
    """
    Extend an auction's end time.
    
    Args:
        auction: Auction instance
        minutes: Minutes to extend by
        
    Returns:
        datetime: New end date/time
    """
    # Calculate new end time
    extension = timedelta(minutes=minutes)
    new_end_date = auction.end_date + extension
    
    # Update auction
    auction.end_date = new_end_date
    auction.save(update_fields=['end_date', 'updated_at'])
    
    # Create notification about extension
    notify_auction_event(auction, 'auction_extended')
    
    return new_end_date


def get_highest_bid(auction) -> Optional[Tuple['Bid', Decimal]]:
    """
    Get the highest bid for an auction.
    
    Args:
        auction: Auction instance
        
    Returns:
        Optional[Tuple['Bid', Decimal]]: Highest bid and amount (None if no bids)
    """
    highest_bid = auction.bids.order_by('-bid_amount').first()
    
    if not highest_bid:
        return None, auction.starting_price
        
    return highest_bid, highest_bid.bid_amount


def calculate_next_minimum_bid(auction) -> Decimal:
    """
    Calculate the next minimum allowed bid for an auction.
    
    Args:
        auction: Auction instance
        
    Returns:
        Decimal: Minimum next bid amount
    """
    _, highest_amount = get_highest_bid(auction)
    return highest_amount + auction.min_bid_increment


def is_auction_reserve_met(auction) -> bool:
    """
    Check if an auction's reserve price has been met.
    
    Args:
        auction: Auction instance
        
    Returns:
        bool: True if reserve is met or no reserve
    """
    # If no reserve price, always met
    if not auction.reserve_price:
        return True
        
    # Check if highest bid meets reserve
    _, highest_amount = get_highest_bid(auction)
    return highest_amount >= auction.reserve_price


def debug_request(view_func):
    """
    Decorator to debug API requests in development.
    
    Args:
        view_func: View function to wrap
        
    Returns:
        function: Wrapped function
    """
    def wrapper(request, *args, **kwargs):
        if getattr(settings, 'DEBUG', False):
            # Log request details
            logger.debug(f"Request to {view_func.__name__}: {request.method} {request.path}")
            logger.debug(f"Request headers: {request.headers}")
            logger.debug(f"Request data: {request.data if hasattr(request, 'data') else None}")
            logger.debug(f"Request query params: {request.query_params if hasattr(request, 'query_params') else None}")
            
        return view_func(request, *args, **kwargs)
    
    return wrapper