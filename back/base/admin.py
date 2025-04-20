from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from django.forms import Textarea, Select
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import (
    Property, Auction, Bid, Document, Contract,
    MessageThread, ThreadParticipant, Message, Notification,
    Media
)

# Generic Media Inline for all models
class MediaInline(GenericTabularInline):
    model = Media
    extra = 1
    fields = ['file', 'name', 'media_type']
    readonly_fields = ['uploaded_at']

# Base Admin Configuration
class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

# Property Admin
@admin.register(Property)
class PropertyAdmin(BaseModelAdmin):
    list_display = [
        'property_number', 
        'title', 
        'get_property_type_display', 
        'city', 
        'owner_display', 
        'status', 
        'is_published',
        'market_value'
    ]
    list_filter = [
        'property_type', 
        'status', 
        'is_published', 
    ]
    search_fields = ['title', 'address', 'city', 'property_number']
    inlines = [MediaInline]
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'property_type', 'description', 'deed_number')
        }),
        (_('Location Details'), {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        (_('Property Specifications'), {
            'fields': ('size_sqm', 'bedrooms', 'bathrooms', 'year_built')
        }),
        (_('Financial Information'), {
            'fields': ('market_value', 'minimum_bid', 'pricing_details')
        }),
        (_('Ownership and Status'), {
            'fields': ('owner', 'is_published', 'is_verified')
        })
    )

    def owner_display(self, obj):
        return obj.owner.get_full_name() if obj.owner else _('No Owner')
    owner_display.short_description = _('Owner')

# Auction Admin
@admin.register(Auction)
class AuctionAdmin(BaseModelAdmin):
    list_display = [
        'title', 
        'auction_type', 
        'status', 
        'start_date', 
        'end_date', 
        'current_bid', 
        'bid_count'
    ]
    list_filter = [
        'auction_type', 
        'status', 
        'start_date',
        'end_date'
    ]
    search_fields = ['title', 'related_property__title']
    inlines = [MediaInline]
    readonly_fields = ['bid_count', 'view_count']

# Bid Admin
@admin.register(Bid)
class BidAdmin(BaseModelAdmin):
    list_display = [
        'auction', 
        'bidder_display', 
        'bid_amount', 
        'bid_time', 
        'status'
    ]
    list_filter = ['status', 'bid_time']
    search_fields = ['auction__title', 'bidder__email']

    def bidder_display(self, obj):
        return obj.bidder.get_full_name() if obj.bidder else _('Unknown')
    bidder_display.short_description = _('Bidder')

# Document Admin
@admin.register(Document)
class DocumentAdmin(BaseModelAdmin):
    list_display = [
        'document_number', 
        'title', 
        'document_type', 
        'verification_status', 
        'uploaded_by_display'
    ]
    list_filter = [
        'document_type', 
        'verification_status', 
    ]
    search_fields = ['title', 'document_number']
    inlines = [MediaInline]

    def uploaded_by_display(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else _('Unknown')
    uploaded_by_display.short_description = _('Uploaded By')

# Contract Admin
@admin.register(Contract)
class ContractAdmin(BaseModelAdmin):
    list_display = [
        'contract_number', 
        'title', 
        'status', 
        'buyer_display', 
        'seller_display', 
        'total_amount'
    ]
    list_filter = [
        'status', 
        'payment_method', 
        'contract_date'
    ]
    search_fields = ['title', 'contract_number']
    inlines = [MediaInline]

    def buyer_display(self, obj):
        return obj.buyer.get_full_name() if obj.buyer else _('Unknown')
    buyer_display.short_description = _('Buyer')

    def seller_display(self, obj):
        return obj.seller.get_full_name() if obj.seller else _('Unknown')
    seller_display.short_description = _('Seller')

# Message Thread Admin
@admin.register(MessageThread)
class MessageThreadAdmin(BaseModelAdmin):
    list_display = [
        'subject', 
        'thread_type', 
        'status', 
        'creator_display', 
        'last_message_at'
    ]
    list_filter = ['thread_type', 'status']
    search_fields = ['subject']

    def creator_display(self, obj):
        return obj.creator.get_full_name() if obj.creator else _('Unknown')
    creator_display.short_description = _('Creator')

# Message Admin
@admin.register(Message)
class MessageAdmin(BaseModelAdmin):
    list_display = [
        'thread', 
        'sender_display', 
        'message_type', 
        'sent_at', 
        'status'
    ]
    list_filter = ['message_type', 'status', 'sent_at']

    def sender_display(self, obj):
        return obj.sender.get_full_name() if obj.sender else _('Unknown')
    sender_display.short_description = _('Sender')

# Notification Admin
@admin.register(Notification)
class NotificationAdmin(BaseModelAdmin):
    list_display = [
        'title', 
        'recipient_display', 
        'notification_type', 
        'is_read', 
        'is_important'
    ]
    list_filter = [
        'notification_type', 
        'is_read', 
        'is_important', 
    ]
    actions = ['mark_as_read']

    def recipient_display(self, obj):
        return obj.recipient.get_full_name() if obj.recipient else _('Unknown')
    recipient_display.short_description = _('Recipient')

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = _("Mark selected notifications as read")

# Media Admin
@admin.register(Media)
class MediaAdmin(BaseModelAdmin):
    list_display = [
        'file', 
        'name', 
        'media_type', 
        'uploaded_at', 
        'content_object_repr'
    ]
    list_filter = ['media_type']
    search_fields = ['name']

    def content_object_repr(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return _('No associated object')
    content_object_repr.short_description = _('Associated Object')

# Admin Site Configuration
admin.site.site_header = _('Real Estate Auction Platform Admin')
admin.site.site_title = _('Platform Admin')
admin.site.index_title = _('Welcome to Real Estate Auction Platform')