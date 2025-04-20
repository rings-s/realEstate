from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from django.forms import Textarea, Select

from .models import (
    Property, Auction, Bid, Document, Contract,
    MessageThread, ThreadParticipant, Message, Notification,
    Media
)

# Register custom admin filters
class PropertyTypeFilter(admin.SimpleListFilter):
    title = _('نوع العقار')
    parameter_name = 'property_type'

    def lookups(self, request, model_admin):
        return Property.PROPERTY_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(property_type=self.value())
        return queryset


class AuctionStatusFilter(admin.SimpleListFilter):
    title = _('حالة المزاد')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return Auction.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


# Inline models for related objects
class MediaInline(admin.TabularInline):
    model = Media
    extra = 1
    fields = ['file', 'name', 'media_type']
    readonly_fields = ['uploaded_at']
    
    def get_content_type_object(self, obj):
        # This method will be needed to properly handle the generic relation
        return obj


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    fields = ['bidder', 'bid_amount', 'bid_time', 'status', 'is_auto_bid']
    readonly_fields = ['bid_time']
    max_num = 10
    can_delete = False


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = ['title', 'document_type', 'verification_status']
    readonly_fields = ['document_number', 'uploaded_at']
    max_num = 5


class ThreadParticipantInline(admin.TabularInline):
    model = ThreadParticipant
    extra = 1
    fields = ['user', 'role', 'is_active']
    

# Main model admins
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['property_number', 'title', 'property_type_display', 'city', 'owner_name', 'status', 'is_published']
    list_filter = [PropertyTypeFilter, 'status', 'is_published', 'is_verified', 'city']
    search_fields = ['title', 'property_number', 'deed_number', 'address', 'description']
    readonly_fields = ['property_number', 'slug', 'created_at', 'updated_at']
    fieldsets = [
        (_('البيانات الأساسية'), {
            'fields': [
                'property_number', 'title', 'property_type', 'status', 'deed_number', 'slug'
            ]
        }),
        (_('الموقع'), {
            'fields': [
                'location', 'address', 'city', 'state', 'postal_code', 'country'
            ]
        }),
        (_('التفاصيل'), {
            'fields': [
                'description', 'features', 'amenities', 'specifications', 'highQualityStreets'
            ]
        }),
        (_('المواصفات'), {
            'fields': [
                'size_sqm', 'bedrooms', 'bathrooms', 'floors', 'parking_spaces', 'year_built'
            ]
        }),
        (_('البيانات المالية'), {
            'fields': [
                'market_value', 'minimum_bid', 'pricing_details'
            ]
        }),
        (_('الملكية والنشر'), {
            'fields': [
                'owner', 'is_published', 'is_featured', 'is_verified'
            ]
        }),
        (_('البيانات الإضافية'), {
            'fields': [
                'metadata', 'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        }),
    ]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
        models.JSONField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
    }
    
    def property_type_display(self, obj):
        return obj.get_property_type_display()
    property_type_display.short_description = _('نوع العقار')
    
    def owner_name(self, obj):
        if obj.owner:
            return obj.owner.get_full_name() or obj.owner.email
        return _('بدون مالك')
    owner_name.short_description = _('المالك')


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ['title', 'property_link', 'auction_type_display', 'status', 'start_date', 'end_date', 'current_bid']
    list_filter = ['auction_type', AuctionStatusFilter, 'is_published', 'is_featured']
    search_fields = ['title', 'description', 'uuid', 'related_property__title']
    readonly_fields = ['uuid', 'bid_count', 'view_count', 'created_at', 'updated_at']
    inlines = [BidInline]
    
    fieldsets = [
        (_('البيانات الأساسية'), {
            'fields': [
                'uuid', 'title', 'auction_type', 'status', 'description'
            ]
        }),
        (_('التواريخ'), {
            'fields': [
                'start_date', 'end_date', 'registration_deadline'
            ]
        }),
        (_('العقار والمزايدات'), {
            'fields': [
                'related_property', 'starting_bid', 'current_bid', 'reserve_price', 'minimum_increment'
            ]
        }),
        (_('الرسوم والشروط'), {
            'fields': [
                'buyer_premium_percent', 'registration_fee', 'deposit_required',
                'terms_conditions', 'special_notes'
            ]
        }),
        (_('البيانات الإحصائية'), {
            'fields': [
                'view_count', 'bid_count', 'registered_bidders'
            ]
        }),
        (_('الإعدادات'), {
            'fields': [
                'is_published', 'is_featured', 'is_private'
            ]
        }),
        (_('البيانات الإضافية'), {
            'fields': [
                'viewing_dates', 'timeline', 'financial_terms', 'analytics',
                'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        }),
    ]
    
    def auction_type_display(self, obj):
        return obj.get_auction_type_display()
    auction_type_display.short_description = _('نوع المزاد')
    
    def property_link(self, obj):
        if obj.related_property:
            url = reverse('admin:auction_platform_property_change', args=[obj.related_property.id])
            return format_html('<a href="{}">{}</a>', url, obj.related_property.title)
        return _('غير مرتبط بعقار')
    property_link.short_description = _('العقار المرتبط')


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['id', 'auction_link', 'bidder_name', 'bid_amount', 'bid_time', 'status']
    list_filter = ['status', 'is_auto_bid']
    search_fields = ['bidder__email', 'bidder__first_name', 'bidder__last_name', 'auction__title']
    readonly_fields = ['bid_time', 'ip_address', 'user_agent', 'created_at', 'updated_at']
    
    fieldsets = [
        (_('البيانات الأساسية'), {
            'fields': [
                'auction', 'bidder', 'bid_amount', 'bid_time', 'status'
            ]
        }),
        (_('المزايدة التلقائية'), {
            'fields': [
                'is_auto_bid', 'max_auto_bid'
            ]
        }),
        (_('معلومات الاتصال'), {
            'fields': [
                'ip_address', 'user_agent'
            ]
        }),
        (_('البيانات الإضافية'), {
            'fields': [
                'notes', 'metadata', 'payment_info', 'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        }),
    ]
    
    def auction_link(self, obj):
        if obj.auction:
            url = reverse('admin:auction_platform_auction_change', args=[obj.auction.id])
            return format_html('<a href="{}">{}</a>', url, obj.auction.title)
        return _('غير مرتبط بمزاد')
    auction_link.short_description = _('المزاد')
    
    def bidder_name(self, obj):
        if obj.bidder:
            return obj.bidder.get_full_name() or obj.bidder.email
        return _('مزايد غير معروف')
    bidder_name.short_description = _('المزايد')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['document_number', 'title', 'document_type_display', 'verification_status', 'uploaded_by_name']
    list_filter = ['document_type', 'verification_status', 'is_public']
    search_fields = ['title', 'document_number', 'description']
    readonly_fields = ['document_number', 'file_size', 'content_type', 'created_at', 'updated_at']
    
    fieldsets = [
        (_('البيانات الأساسية'), {
            'fields': [
                'document_number', 'title', 'document_type', 'description'
            ]
        }),
        (_('التحقق'), {
            'fields': [
                'verification_status', 'verification_notes', 'verification_details',
                'verified_by', 'verification_date'
            ]
        }),
        (_('التواريخ'), {
            'fields': [
                'issue_date', 'expiry_date'
            ]
        }),
        (_('العلاقات'), {
            'fields': [
                'related_property', 'related_auction', 'related_contract', 'uploaded_by'
            ]
        }),
        (_('الوصول'), {
            'fields': [
                'is_public', 'access_code'
            ]
        }),
        (_('البيانات الفنية'), {
            'fields': [
                'file_size', 'content_type', 'document_metadata', 'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        }),
    ]
    
    def document_type_display(self, obj):
        return obj.get_document_type_display()
    document_type_display.short_description = _('نوع الوثيقة')
    
    def uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.email
        return _('غير معروف')
    uploaded_by_name.short_description = _('تم التحميل بواسطة')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'title', 'property_link', 'status', 'total_amount', 'contract_date']
    list_filter = ['status', 'payment_method', 'is_verified']
    search_fields = ['title', 'contract_number', 'description']
    readonly_fields = ['contract_number', 'verification_date', 'buyer_signed_date', 'seller_signed_date', 'created_at', 'updated_at']
    inlines = [DocumentInline]
    
    fieldsets = [
        (_('البيانات الأساسية'), {
            'fields': [
                'contract_number', 'title', 'description', 'status'
            ]
        }),
        (_('العلاقات'), {
            'fields': [
                'related_property', 'related_auction', 'buyer', 'seller'
            ]
        }),
        (_('التواريخ'), {
            'fields': [
                'contract_date', 'effective_date', 'expiry_date', 'timeline'
            ]
        }),
        (_('البيانات المالية'), {
            'fields': [
                'total_amount', 'down_payment', 'payment_method', 'payment_terms',
                'payment_details', 'payments_history'
            ]
        }),
        (_('التحقق والتوقيع'), {
            'fields': [
                'is_verified', 'verified_by', 'verification_date',
                'buyer_signed', 'buyer_signed_date', 'seller_signed', 'seller_signed_date'
            ]
        }),
        (_('البيانات الإضافية'), {
            'fields': [
                'special_conditions', 'parties', 'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        }),
    ]
    
    def property_link(self, obj):
        if obj.related_property:
            url = reverse('admin:auction_platform_property_change', args=[obj.related_property.id])
            return format_html('<a href="{}">{}</a>', url, obj.related_property.title)
        return _('غير مرتبط بعقار')
    property_link.short_description = _('العقار المرتبط')


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ['subject', 'thread_type_display', 'status', 'creator_name', 'last_message_at']
    list_filter = ['thread_type', 'status', 'is_private', 'is_system_thread']
    search_fields = ['subject', 'uuid']
    readonly_fields = ['uuid', 'last_message_at', 'created_at', 'updated_at']
    inlines = [ThreadParticipantInline]
    
    fieldsets = [
        (_('البيانات الأساسية'), {
            'fields': [
                'uuid', 'subject', 'thread_type', 'status'
            ]
        }),
        (_('العلاقات'), {
            'fields': [
                'creator', 'related_property', 'related_auction'
            ]
        }),
        (_('الإعدادات'), {
            'fields': [
                'is_private', 'is_system_thread'
            ]
        }),
        (_('البيانات الإضافية'), {
            'fields': [
                'last_message_at', 'metadata', 'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        }),
    ]
    
    def thread_type_display(self, obj):
        return obj.get_thread_type_display()
    thread_type_display.short_description = _('نوع المحادثة')
    
    def creator_name(self, obj):
        if obj.creator:
            return obj.creator.get_full_name() or obj.creator.email
        return _('غير معروف')
    creator_name.short_description = _('المنشئ')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'thread_subject', 'sender_name', 'content_preview', 'sent_at', 'status']
    list_filter = ['message_type', 'status', 'is_system_message', 'is_important']
    search_fields = ['content', 'thread__subject', 'sender__email']
    readonly_fields = ['sent_at', 'delivered_at', 'read_at', 'created_at', 'updated_at']
    
    fieldsets = [
        (_('البيانات الأساسية'), {
            'fields': [
                'thread', 'sender', 'content', 'message_type', 'status'
            ]
        }),
        (_('المرفقات'), {
            'fields': [
                'attachment_name', 'attachment_size'
            ]
        }),
        (_('الردود'), {
            'fields': [
                'reply_to'
            ]
        }),
        (_('التواريخ'), {
            'fields': [
                'sent_at', 'delivered_at', 'read_at'
            ]
        }),
        (_('الإعدادات'), {
            'fields': [
                'is_system_message', 'is_important'
            ]
        }),
        (_('البيانات الإضافية'), {
            'fields': [
                'metadata', 'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        }),
    ]
    
    def thread_subject(self, obj):
        if obj.thread:
            url = reverse('admin:auction_platform_messagethread_change', args=[obj.thread.id])
            return format_html('<a href="{}">{}</a>', url, obj.thread.subject)
        return _('غير مرتبط بمحادثة')
    thread_subject.short_description = _('المحادثة')
    
    def sender_name(self, obj):
        if obj.sender:
            return obj.sender.get_full_name() or obj.sender.email
        return _('غير معروف')
    sender_name.short_description = _('المرسل')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = _('المحتوى')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient_name', 'notification_type', 'is_read', 'sent_at']
    list_filter = ['notification_type', 'is_read', 'is_sent', 'is_important']
    search_fields = ['title', 'content', 'recipient__email']
    readonly_fields = ['read_at', 'sent_at', 'created_at', 'updated_at']
    
    fieldsets = [
        (_('البيانات الأساسية'), {
            'fields': [
                'recipient', 'notification_type', 'title', 'content', 'channel'
            ]
        }),
        (_('الحالة'), {
            'fields': [
                'is_read', 'read_at', 'is_sent', 'sent_at'
            ]
        }),
        (_('العلاقات'), {
            'fields': [
                'related_thread', 'related_auction', 'related_property', 'related_contract'
            ]
        }),
        (_('الإعدادات'), {
            'fields': [
                'action_url', 'is_important', 'expiry_date'
            ]
        }),
        (_('البيانات الإضافية'), {
            'fields': [
                'notification_data', 'created_at', 'updated_at'
            ],
            'classes': ['collapse']
        }),
    ]
    
    def recipient_name(self, obj):
        if obj.recipient:
            return obj.recipient.get_full_name() or obj.recipient.email
        return _('غير معروف')
    recipient_name.short_description = _('المستلم')


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'file', 'media_type', 'content_object_repr', 'uploaded_at']
    list_filter = ['media_type', 'uploaded_at']
    search_fields = ['name', 'file']
    readonly_fields = ['uploaded_at']
    
    def content_object_repr(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return _('غير مرتبط')
    content_object_repr.short_description = _('المرتبط بـ')


# Custom admin site configuration
admin.site.site_header = _('منصة المزاد العقاري - لوحة الإدارة')
admin.site.site_title = _('إدارة منصة المزاد')
admin.site.index_title = _('مرحباً بك في لوحة إدارة المزادات العقارية')