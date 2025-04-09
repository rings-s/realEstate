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
    readonly_fields = ('width', 'height', 'file_size')


class AuctionImageInline(admin.TabularInline):
    model = AuctionImage
    extra = 1
    fields = ('image', 'is_primary', 'order', 'caption', 'alt_text')
    readonly_fields = ('width', 'height', 'file_size')


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    fields = ('bidder', 'bid_amount', 'bid_time', 'status', 'is_auto_bid', 'max_auto_bid')
    readonly_fields = ('bid_time',)
    can_delete = False
    ordering = ('-bid_time',)
    max_num = 20
    classes = ('collapse',)


class ThreadParticipantInline(admin.TabularInline):
    model = ThreadParticipant
    extra = 1
    fields = ('user', 'role', 'is_active', 'is_muted', 'last_read_at')
    readonly_fields = ('last_read_at',)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('sender', 'content', 'message_type', 'status', 'sent_at', 'read_at')
    readonly_fields = ('sent_at', 'read_at')
    can_delete = False
    ordering = ('sent_at',)
    max_num = 20
    classes = ('collapse',)


class PropertyViewInline(admin.TabularInline):
    model = PropertyView
    extra = 1
    fields = ('view_type', 'image', 'file', 'external_url')


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1
    fields = ('title', 'document_type', 'file', 'is_public', 'verification_status')
    readonly_fields = ('document_number', 'file_size', 'verification_date')
    max_num = 10
    classes = ('collapse',)


# -------------------------------------------------------------------------
# Admin Classes
# -------------------------------------------------------------------------

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('property_number', 'title', 'property_type', 'status', 'city',
                    'owner', 'is_published', 'is_featured', 'is_verified', 'created_at')
    list_filter = ('property_type', 'status', 'city', 'is_published', 'is_featured', 'is_verified')
    search_fields = ('property_number', 'title', 'owner__email', 'owner__first_name', 'owner__last_name', 'address', 'city')
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
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [PropertyImageInline, DocumentInline]
    list_per_page = 25
    save_on_top = True
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
    list_display = ('id', 'property_title', 'is_primary', 'order', 'image_thumbnail', 'created_at')
    list_filter = ('is_primary', 'property__property_type')
    search_fields = ('property__title', 'caption', 'alt_text')
    readonly_fields = ('width', 'height', 'file_size', 'created_at', 'updated_at', 'image_preview')
    fields = ('property', 'image', 'image_preview', 'is_primary', 'order', 'caption', 'alt_text',
              'width', 'height', 'file_size', 'metadata', 'created_at', 'updated_at')

    def property_title(self, obj):
        return obj.property.title

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "-"
    image_thumbnail.short_description = _("Thumbnail")

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" />', obj.image.url)
        return "-"
    image_preview.short_description = _("Image Preview")


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'auction_type', 'status', 'related_property_link',
                    'starting_bid', 'current_bid', 'start_date', 'end_date', 'is_published')
    list_filter = ('auction_type', 'status', 'is_published', 'is_featured', 'is_private')
    search_fields = ('title', 'description', 'related_property__title')
    readonly_fields = ('uuid', 'current_bid', 'bid_count', 'view_count', 'registered_bidders',
                       'created_at', 'updated_at', 'time_remaining')
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
        (_('Bidding History'), {
            'fields': ('bid_history', 'bid_count'),
            'classes': ('collapse',)
        }),
        (_('Publication'), {
            'fields': ('is_published', 'is_featured', 'is_private', 'cover_image')
        }),
        (_('Terms & Details'), {
            'fields': ('terms_conditions', 'special_notes', 'financial_terms'),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('view_count', 'registered_bidders', 'time_remaining', 'analytics'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [AuctionImageInline, BidInline, PropertyViewInline, DocumentInline]
    list_per_page = 25
    save_on_top = True
    actions = ['update_auction_status', 'mark_as_published', 'mark_as_featured']

    def related_property_link(self, obj):
        if obj.related_property:
            url = reverse('admin:auction_platform_property_change', args=[obj.related_property.id])
            return format_html('<a href="{}">{}</a>', url, obj.related_property.title)
        return "-"
    related_property_link.short_description = _("Related Property")

    def time_remaining(self, obj):
        if obj.end_date > timezone.now():
            time_left = obj.end_date - timezone.now()
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{days} days, {hours} hours, {minutes} minutes"
        return _("Auction ended")
    time_remaining.short_description = _("Time Remaining")

    def update_auction_status(self, request, queryset):
        from .utils import check_auction_status
        for auction in queryset:
            check_auction_status(auction)
    update_auction_status.short_description = _("Update auction status based on dates")

    def mark_as_published(self, request, queryset):
        queryset.update(is_published=True)
    mark_as_published.short_description = _("Mark selected auctions as published")

    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
    mark_as_featured.short_description = _("Mark selected auctions as featured")


@admin.register(AuctionImage)
class AuctionImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'auction_title', 'is_primary', 'order', 'image_thumbnail', 'created_at')
    list_filter = ('is_primary', 'auction__auction_type')
    search_fields = ('auction__title', 'caption', 'alt_text')
    readonly_fields = ('width', 'height', 'file_size', 'created_at', 'updated_at', 'image_preview')
    fields = ('auction', 'image', 'image_preview', 'is_primary', 'order', 'caption', 'alt_text',
              'width', 'height', 'file_size', 'metadata', 'created_at', 'updated_at')

    def auction_title(self, obj):
        return obj.auction.title

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "-"
    image_thumbnail.short_description = _("Thumbnail")

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" />', obj.image.url)
        return "-"
    image_preview.short_description = _("Image Preview")


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('id', 'auction_link', 'bidder_link', 'bid_amount', 'bid_time',
                    'status', 'is_auto_bid', 'max_auto_bid', 'ip_address')
    list_filter = ('status', 'is_auto_bid', 'bid_time', 'auction__title')
    search_fields = ('bidder__email', 'bidder__first_name', 'bidder__last_name',
                     'auction__title', 'notes')
    readonly_fields = ('bid_time', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('auction', 'bidder', 'bid_amount', 'bid_time', 'status')
        }),
        (_('Auto Bidding'), {
            'fields': ('is_auto_bid', 'max_auto_bid'),
            'classes': ('collapse',)
        }),
        (_('Tracking'), {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'payment_info', 'metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 25
    actions = ['mark_as_winning', 'mark_as_outbid', 'mark_as_rejected']

    def auction_link(self, obj):
        if obj.auction:
            url = reverse('admin:auction_platform_auction_change', args=[obj.auction.id])
            return format_html('<a href="{}">{}</a>', url, obj.auction.title)
        return "-"
    auction_link.short_description = _("Auction")

    def bidder_link(self, obj):
        if obj.bidder:
            url = reverse('admin:accounts_customuser_change', args=[obj.bidder.id])
            return format_html('<a href="{}">{}</a>', url, obj.bidder.email)
        return "-"
    bidder_link.short_description = _("Bidder")

    def mark_as_winning(self, request, queryset):
        # Mark all other bids for the same auctions as outbid
        for bid in queryset:
            Bid.objects.filter(auction=bid.auction, status='winning').exclude(id=bid.id).update(status='outbid')

        queryset.update(status='winning')

        # Update auction current bid
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
    list_display = ('document_number', 'title', 'document_type', 'uploaded_by_link',
                    'verification_status', 'is_public', 'file_size_kb', 'created_at')
    list_filter = ('document_type', 'verification_status', 'is_public', 'created_at')
    search_fields = ('document_number', 'title', 'description', 'uploaded_by__email')
    readonly_fields = ('document_number', 'file_size', 'page_count', 'content_type',
                       'verification_date', 'created_at', 'updated_at', 'thumbnail_preview')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('document_number', 'title', 'document_type', 'description', 'file')
        }),
        (_('Relations'), {
            'fields': ('related_property', 'related_auction', 'related_contract')
        }),
        (_('Verification'), {
            'fields': ('verification_status', 'verification_notes', 'verification_details',
                      'verified_by', 'verification_date')
        }),
        (_('Dates'), {
            'fields': ('issue_date', 'expiry_date')
        }),
        (_('Upload Information'), {
            'fields': ('uploaded_by', 'file_size', 'page_count', 'content_type', 'thumbnail', 'thumbnail_preview')
        }),
        (_('Access Control'), {
            'fields': ('is_public', 'access_code')
        }),
        (_('Metadata'), {
            'fields': ('document_metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 25
    actions = ['mark_as_verified', 'mark_as_public', 'mark_as_private']

    def uploaded_by_link(self, obj):
        if obj.uploaded_by:
            url = reverse('admin:accounts_customuser_change', args=[obj.uploaded_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.uploaded_by.email)
        return "-"
    uploaded_by_link.short_description = _("Uploaded By")

    def file_size_kb(self, obj):
        if obj.file_size:
            return f"{obj.file_size} KB"
        return "-"
    file_size_kb.short_description = _("File Size")

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="200" />', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = _("Thumbnail Preview")

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
    list_display = ('contract_number', 'title', 'status', 'related_property_link',
                    'buyer_link', 'seller_link', 'total_amount', 'contract_date')
    list_filter = ('status', 'payment_method', 'is_verified', 'contract_date')
    search_fields = ('contract_number', 'title', 'buyer__email', 'seller__email')
    readonly_fields = ('contract_number', 'verification_date', 'buyer_signed_date',
                       'seller_signed_date', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('contract_number', 'title', 'description', 'status', 'contract_file')
        }),
        (_('Relations'), {
            'fields': ('related_property', 'related_auction')
        }),
        (_('Parties'), {
            'fields': ('buyer', 'seller', 'parties')
        }),
        (_('Dates'), {
            'fields': ('contract_date', 'effective_date', 'expiry_date', 'timeline')
        }),
        (_('Financial'), {
            'fields': ('total_amount', 'down_payment', 'payment_method', 'payment_terms',
                      'payment_details', 'payments_history')
        }),
        (_('Terms'), {
            'fields': ('special_conditions',)
        }),
        (_('Verification'), {
            'fields': ('is_verified', 'verified_by', 'verification_date')
        }),
        (_('Signatures'), {
            'fields': ('buyer_signed', 'buyer_signed_date', 'seller_signed', 'seller_signed_date')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [DocumentInline]
    list_per_page = 25
    actions = ['mark_as_active', 'mark_as_fulfilled', 'mark_as_verified']

    def related_property_link(self, obj):
        if obj.related_property:
            url = reverse('admin:auction_platform_property_change', args=[obj.related_property.id])
            return format_html('<a href="{}">{}</a>', url, obj.related_property.title)
        return "-"
    related_property_link.short_description = _("Property")

    def buyer_link(self, obj):
        if obj.buyer:
            url = reverse('admin:accounts_customuser_change', args=[obj.buyer.id])
            return format_html('<a href="{}">{}</a>', url, obj.buyer.email)
        return "-"
    buyer_link.short_description = _("Buyer")

    def seller_link(self, obj):
        if obj.seller:
            url = reverse('admin:accounts_customuser_change', args=[obj.seller.id])
            return format_html('<a href="{}">{}</a>', url, obj.seller.email)
        return "-"
    seller_link.short_description = _("Seller")

    def mark_as_active(self, request, queryset):
        queryset.update(status='active')

        # Update property status
        for contract in queryset:
            if contract.related_property:
                contract.related_property.status = 'under_contract'
                contract.related_property.save(update_fields=['status'])
    mark_as_active.short_description = _("Mark selected contracts as active")

    def mark_as_fulfilled(self, request, queryset):
        queryset.update(status='fulfilled')

        # Update property status
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
    list_display = ('id', 'subject', 'thread_type', 'status', 'creator_link',
                    'participant_count', 'message_count', 'last_message_at')
    list_filter = ('thread_type', 'status', 'is_private', 'is_system_thread', 'created_at')
    search_fields = ('subject', 'creator__email', 'participants__user__email')
    readonly_fields = ('uuid', 'last_message_at', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('uuid', 'subject', 'thread_type', 'status')
        }),
        (_('Relations'), {
            'fields': ('creator', 'related_property', 'related_auction')
        }),
        (_('Settings'), {
            'fields': ('is_private', 'is_system_thread')
        }),
        (_('Activity'), {
            'fields': ('last_message_at',)
        }),
        (_('Metadata'), {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ThreadParticipantInline, MessageInline]
    list_per_page = 25
    actions = ['mark_as_active', 'mark_as_closed', 'mark_as_archived']

    def creator_link(self, obj):
        if obj.creator:
            url = reverse('admin:accounts_customuser_change', args=[obj.creator.id])
            return format_html('<a href="{}">{}</a>', url, obj.creator.email)
        return "-"
    creator_link.short_description = _("Creator")

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = _("Participants")

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = _("Messages")

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
    list_display = ('id', 'thread_link', 'user_link', 'role_display', 'is_active', 'is_muted', 'last_read_at')
    list_filter = ('is_active', 'is_muted', 'created_at')
    search_fields = ('thread__subject', 'user__email')
    readonly_fields = ('last_read_at', 'created_at', 'updated_at')
    fields = ('thread', 'user', 'role', 'is_active', 'is_muted', 'last_read_at',
              'custom_permissions', 'created_at', 'updated_at')

    def thread_link(self, obj):
        if obj.thread:
            url = reverse('admin:auction_platform_messagethread_change', args=[obj.thread.id])
            return format_html('<a href="{}">{}</a>', url, obj.thread.subject)
        return "-"
    thread_link.short_description = _("Thread")

    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return "-"
    user_link.short_description = _("User")

    def role_display(self, obj):
        if obj.role:
            return obj.role.get_name_display()
        return "-"
    role_display.short_description = _("Role")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread_link', 'sender_link', 'message_preview',
                    'message_type', 'status', 'sent_at', 'read_at')
    list_filter = ('message_type', 'status', 'is_system_message', 'is_important', 'sent_at')
    search_fields = ('content', 'sender__email', 'thread__subject')
    readonly_fields = ('sent_at', 'delivered_at', 'read_at', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('thread', 'sender', 'content', 'message_type', 'status')
        }),
        (_('Attachment'), {
            'fields': ('attachment', 'attachment_type', 'attachment_name', 'attachment_size'),
            'classes': ('collapse',)
        }),
        (_('Reply'), {
            'fields': ('reply_to',),
            'classes': ('collapse',)
        }),
        (_('Timing'), {
            'fields': ('sent_at', 'delivered_at', 'read_at')
        }),
        (_('Flags'), {
            'fields': ('is_system_message', 'is_important')
        }),
        (_('Metadata'), {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50
    actions = ['mark_as_delivered', 'mark_as_read', 'mark_as_important']

    def thread_link(self, obj):
        if obj.thread:
            url = reverse('admin:auction_platform_messagethread_change', args=[obj.thread.id])
            return format_html('<a href="{}">{}</a>', url, obj.thread.subject)
        return "-"
    thread_link.short_description = _("Thread")

    def sender_link(self, obj):
        if obj.sender:
            url = reverse('admin:accounts_customuser_change', args=[obj.sender.id])
            return format_html('<a href="{}">{}</a>', url, obj.sender.email)
        elif obj.is_system_message:
            return _("System")
        return "-"
    sender_link.short_description = _("Sender")

    def message_preview(self, obj):
        return (obj.content[:50] + '...') if len(obj.content) > 50 else obj.content
    message_preview.short_description = _("Message")

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
    list_display = ('id', 'auction_link', 'view_type', 'size_sqm', 'has_image', 'has_file', 'created_at')
    list_filter = ('view_type', 'created_at')
    search_fields = ('auction__title', 'address', 'legal_description')
    readonly_fields = ('created_at', 'updated_at', 'image_preview', 'file_link')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('auction', 'view_type')
        }),
        (_('Location & Size'), {
            'fields': ('location', 'dimensions', 'address', 'legal_description', 'size_sqm', 'elevation')
        }),
        (_('Media'), {
            'fields': ('image', 'image_preview', 'file', 'file_link')
        }),
        (_('External Content'), {
            'fields': ('external_url', 'embed_code')
        }),
        (_('Configuration'), {
            'fields': ('view_config', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def auction_link(self, obj):
        if obj.auction:
            url = reverse('admin:auction_platform_auction_change', args=[obj.auction.id])
            return format_html('<a href="{}">{}</a>', url, obj.auction.title)
        return "-"
    auction_link.short_description = _("Auction")

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = _("Has Image")

    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = _("Has File")

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" />', obj.image.url)
        return "-"
    image_preview.short_description = _("Image Preview")

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.file.url, obj.file.name)
        return "-"
    file_link.short_description = _("File Link")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient_link', 'notification_type', 'title_preview',
                    'is_read', 'is_sent', 'channel', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_sent', 'is_important', 'channel', 'created_at')
    search_fields = ('title', 'content', 'recipient__email', 'action_url')
    readonly_fields = ('read_at', 'sent_at', 'created_at', 'updated_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('recipient', 'notification_type', 'title', 'content', 'channel')
        }),
        (_('Status'), {
            'fields': ('is_read', 'read_at', 'is_sent', 'sent_at')
        }),
        (_('Relations'), {
            'fields': ('related_thread', 'related_auction', 'related_property', 'related_contract')
        }),
        (_('Action'), {
            'fields': ('action_url', 'is_important', 'expiry_date')
        }),
        (_('Metadata'), {
            'fields': ('notification_data', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50
    actions = ['mark_as_read', 'mark_as_sent', 'mark_as_important']

    def recipient_link(self, obj):
        if obj.recipient:
            url = reverse('admin:accounts_customuser_change', args=[obj.recipient.id])
            return format_html('<a href="{}">{}</a>', url, obj.recipient.email)
        return "-"
    recipient_link.short_description = _("Recipient")

    def title_preview(self, obj):
        return (obj.title[:50] + '...') if len(obj.title) > 50 else obj.title
    title_preview.short_description = _("Title")

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True, read_at=timezone.now())
    mark_as_read.short_description = _("Mark selected notifications as read")

    def mark_as_sent(self, request, queryset):
        queryset.update(is_sent=True, sent_at=timezone.now())
    mark_as_sent.short_description = _("Mark selected notifications as sent")

    def mark_as_important(self, request, queryset):
        queryset.update(is_important=True)
    mark_as_important.short_description = _("Mark selected notifications as important")
