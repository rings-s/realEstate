from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone

from .models import (
    Property, PropertyImage, Auction, AuctionImage, Bid,
    Document, Contract, MessageThread, ThreadParticipant, Message,
    PropertyView, Notification
)


# -------------------------------------------------------------------------
# Inline Admin Classes
# -------------------------------------------------------------------------

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image', 'is_primary', 'order', 'caption', 'alt_text')


class AuctionImageInline(admin.TabularInline):
    model = AuctionImage
    extra = 1
    fields = ('image', 'is_primary', 'order', 'caption', 'alt_text')


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    fields = ('bidder', 'bid_amount', 'bid_time', 'status')
    readonly_fields = ('bid_time',)
    can_delete = False


class ThreadParticipantInline(admin.TabularInline):
    model = ThreadParticipant
    extra = 1
    fields = ('user', 'role', 'is_active', 'is_muted')


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('sender', 'content', 'message_type', 'status', 'sent_at')
    readonly_fields = ('sent_at',)
    can_delete = False


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1
    fields = ('title', 'document_type', 'file', 'verification_status')


# -------------------------------------------------------------------------
# Admin Classes
# -------------------------------------------------------------------------

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('property_number', 'title', 'property_type', 'status', 'city', 'owner', 'is_published')
    list_filter = ('property_type', 'status', 'city', 'is_published', 'is_featured')
    search_fields = ('property_number', 'title', 'owner__email', 'address', 'city')
    readonly_fields = ('property_number', 'slug', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('property_number', 'title', 'property_type', 'status', 'description', 'owner')
        }),
        (_('Location'), {
            'fields': ('address', 'city', 'state', 'postal_code', 'country', 'location')
        }),
        (_('Features'), {
            'fields': ('size_sqm', 'bedrooms', 'bathrooms', 'parking_spaces', 'year_built',
                      'features', 'amenities', 'rooms', 'specifications')
        }),
        (_('Financial'), {
            'fields': ('market_value', 'minimum_bid', 'pricing_details')
        }),
        (_('Publication'), {
            'fields': ('is_published', 'is_featured', 'is_verified', 'cover_image', 'slug')
        }),
    )
    inlines = [PropertyImageInline, DocumentInline]
    actions = ['mark_as_published', 'mark_as_featured', 'mark_as_verified']

    def mark_as_published(self, request, queryset):
        queryset.update(is_published=True)
    mark_as_published.short_description = _("Mark selected properties as published")

    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
    mark_as_featured.short_description = _("Mark selected properties as featured")

    def mark_as_verified(self, request, queryset):
        queryset.update(is_verified=True)
    mark_as_verified.short_description = _("Mark selected properties as verified")


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'property__property_type')
    search_fields = ('property__title', 'caption', 'alt_text')
    readonly_fields = ('width', 'height', 'file_size', 'created_at', 'updated_at')


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'auction_type', 'status', 'related_property',
                    'starting_bid', 'current_bid', 'start_date', 'end_date', 'is_published')
    list_filter = ('auction_type', 'status', 'is_published', 'is_featured')
    search_fields = ('title', 'description', 'related_property__title')
    readonly_fields = ('uuid', 'current_bid', 'bid_count', 'view_count', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('uuid', 'title', 'auction_type', 'status', 'description', 'related_property')
        }),
        (_('Schedule'), {
            'fields': ('start_date', 'end_date', 'registration_deadline', 'viewing_dates', 'timeline')
        }),
        (_('Financial'), {
            'fields': ('starting_bid', 'reserve_price', 'minimum_increment', 'current_bid',
                      'estimated_value', 'buyer_premium_percent', 'registration_fee', 'deposit_required')
        }),
        (_('Publication'), {
            'fields': ('is_published', 'is_featured', 'is_private', 'cover_image')
        }),
        (_('Terms & Details'), {
            'fields': ('terms_conditions', 'special_notes', 'financial_terms')
        }),
    )
    inlines = [AuctionImageInline, BidInline, DocumentInline]
    actions = ['update_auction_status', 'mark_as_published', 'mark_as_featured']

    def update_auction_status(self, request, queryset):
        now = timezone.now()
        for auction in queryset:
            if auction.start_date <= now and auction.end_date > now:
                auction.status = 'live'
                auction.save(update_fields=['status'])
            elif auction.end_date <= now:
                auction.status = 'ended'
                auction.save(update_fields=['status'])
            elif auction.start_date > now and auction.status == 'draft':
                auction.status = 'scheduled'
                auction.save(update_fields=['status'])
    update_auction_status.short_description = _("Update auction status based on dates")

    def mark_as_published(self, request, queryset):
        queryset.update(is_published=True)
    mark_as_published.short_description = _("Mark selected auctions as published")

    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
    mark_as_featured.short_description = _("Mark selected auctions as featured")


@admin.register(AuctionImage)
class AuctionImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'auction', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'auction__auction_type')
    search_fields = ('auction__title', 'caption', 'alt_text')
    readonly_fields = ('width', 'height', 'file_size', 'created_at', 'updated_at')


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('id', 'auction', 'bidder', 'bid_amount', 'bid_time', 'status', 'is_auto_bid')
    list_filter = ('status', 'is_auto_bid', 'bid_time')
    search_fields = ('bidder__email', 'auction__title', 'notes')
    readonly_fields = ('bid_time', 'created_at', 'updated_at')
    actions = ['mark_as_winning', 'mark_as_outbid', 'mark_as_rejected']

    def mark_as_winning(self, request, queryset):
        for bid in queryset:
            Bid.objects.filter(auction=bid.auction, status='winning').exclude(id=bid.id).update(status='outbid')
        queryset.update(status='winning')
        for bid in queryset:
            bid.auction.current_bid = bid.bid_amount
            bid.auction.save(update_fields=['current_bid'])
    mark_as_winning.short_description = _("Mark selected bids as winning")

    def mark_as_outbid(self, request, queryset):
        queryset.update(status='outbid')
    mark_as_outbid.short_description = _("Mark selected bids as outbid")

    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected')
    mark_as_rejected.short_description = _("Mark selected bids as rejected")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'title', 'document_type', 'uploaded_by',
                    'verification_status', 'is_public', 'created_at')
    list_filter = ('document_type', 'verification_status', 'is_public')
    search_fields = ('document_number', 'title', 'description', 'uploaded_by__email')
    readonly_fields = ('document_number', 'file_size', 'verification_date', 'created_at', 'updated_at')
    actions = ['mark_as_verified', 'mark_as_public', 'mark_as_private']

    def mark_as_verified(self, request, queryset):
        queryset.update(
            verification_status='verified',
            verification_date=timezone.now(),
            verified_by=request.user
        )
    mark_as_verified.short_description = _("Mark selected documents as verified")

    def mark_as_public(self, request, queryset):
        queryset.update(is_public=True)
    mark_as_public.short_description = _("Mark selected documents as public")

    def mark_as_private(self, request, queryset):
        queryset.update(is_public=False)
    mark_as_private.short_description = _("Mark selected documents as private")


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'title', 'status', 'related_property',
                    'buyer', 'seller', 'total_amount', 'contract_date')
    list_filter = ('status', 'payment_method', 'is_verified', 'contract_date')
    search_fields = ('contract_number', 'title', 'buyer__email', 'seller__email')
    readonly_fields = ('contract_number', 'verification_date', 'buyer_signed_date',
                     'seller_signed_date', 'created_at', 'updated_at')
    inlines = [DocumentInline]
    actions = ['mark_as_active', 'mark_as_fulfilled', 'mark_as_verified']

    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
        for contract in queryset:
            if contract.related_property:
                contract.related_property.status = 'under_contract'
                contract.related_property.save(update_fields=['status'])
    mark_as_active.short_description = _("Mark selected contracts as active")

    def mark_as_fulfilled(self, request, queryset):
        queryset.update(status='fulfilled')
        for contract in queryset:
            if contract.related_property:
                contract.related_property.status = 'sold'
                contract.related_property.save(update_fields=['status'])
    mark_as_fulfilled.short_description = _("Mark selected contracts as fulfilled")

    def mark_as_verified(self, request, queryset):
        queryset.update(
            is_verified=True,
            verification_date=timezone.now(),
            verified_by=request.user
        )
    mark_as_verified.short_description = _("Mark selected contracts as verified")


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'thread_type', 'status', 'creator', 'last_message_at')
    list_filter = ('thread_type', 'status', 'is_private', 'is_system_thread', 'created_at')
    search_fields = ('subject', 'creator__email')
    readonly_fields = ('uuid', 'last_message_at', 'created_at', 'updated_at')
    inlines = [ThreadParticipantInline, MessageInline]
    actions = ['mark_as_active', 'mark_as_closed', 'mark_as_archived']

    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
    mark_as_active.short_description = _("Mark selected threads as active")

    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_as_closed.short_description = _("Mark selected threads as closed")

    def mark_as_archived(self, request, queryset):
        queryset.update(status='archived')
    mark_as_archived.short_description = _("Mark selected threads as archived")


@admin.register(ThreadParticipant)
class ThreadParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'user', 'role', 'is_active', 'is_muted', 'last_read_at')
    list_filter = ('is_active', 'is_muted', 'created_at')
    search_fields = ('thread__subject', 'user__email')
    readonly_fields = ('last_read_at', 'created_at', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'sender', 'message_type', 'status', 'sent_at', 'read_at')
    list_filter = ('message_type', 'status', 'is_system_message', 'is_important', 'sent_at')
    search_fields = ('content', 'sender__email', 'thread__subject')
    readonly_fields = ('sent_at', 'delivered_at', 'read_at', 'created_at', 'updated_at')
    actions = ['mark_as_delivered', 'mark_as_read', 'mark_as_important']

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered', delivered_at=timezone.now())
    mark_as_delivered.short_description = _("Mark selected messages as delivered")

    def mark_as_read(self, request, queryset):
        queryset.update(status='read', read_at=timezone.now())
    mark_as_read.short_description = _("Mark selected messages as read")

    def mark_as_important(self, request, queryset):
        queryset.update(is_important=True)
    mark_as_important.short_description = _("Mark selected messages as important")


@admin.register(PropertyView)
class PropertyViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'auction', 'view_type', 'size_sqm', 'created_at')
    list_filter = ('view_type', 'created_at')
    search_fields = ('auction__title', 'address', 'legal_description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'notification_type', 'title', 'is_read', 'is_sent', 'channel', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_sent', 'is_important', 'channel', 'created_at')
    search_fields = ('title', 'content', 'recipient__email', 'action_url')
    readonly_fields = ('read_at', 'sent_at', 'created_at', 'updated_at')
    actions = ['mark_as_read', 'mark_as_sent', 'mark_as_important']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True, read_at=timezone.now())
    mark_as_read.short_description = _("Mark selected notifications as read")

    def mark_as_sent(self, request, queryset):
        queryset.update(is_sent=True, sent_at=timezone.now())
    mark_as_sent.short_description = _("Mark selected notifications as sent")

    def mark_as_important(self, request, queryset):
        queryset.update(is_important=True)
    mark_as_important.short_description = _("Mark selected notifications as important")
