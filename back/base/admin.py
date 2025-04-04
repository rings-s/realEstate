from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    ThreadParticipant, MessageThread, Message,
    Property, Auction, Contract, Bid, Document,
    Payment, Transaction, PropertyView, Notification
)
from accounts.models import Role


class RoleFilter(admin.SimpleListFilter):
    """Filter ThreadParticipants by Role"""
    title = _('دور المستخدم')
    parameter_name = 'role_name'

    def lookups(self, request, model_admin):
        roles = Role.objects.all()
        return [(role.name, role.get_name_display()) for role in roles]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role__name=self.value())
        return queryset


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ['sender', 'content', 'message_type', 'status', 'sent_at', 'read_at']
    readonly_fields = ['sender', 'content', 'message_type', 'status', 'sent_at', 'read_at']
    can_delete = False
    max_num = 10
    ordering = ['-sent_at']

    def has_add_permission(self, request, obj=None):
        return False


class ThreadParticipantInline(admin.TabularInline):
    model = ThreadParticipant
    extra = 1
    fields = ['user', 'role', 'is_active', 'is_muted', 'last_read_at']
    autocomplete_fields = ['user', 'role']
    readonly_fields = ['last_read_at']


@admin.register(ThreadParticipant)
class ThreadParticipantAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_user_email', 'get_thread_subject',
        'get_role_name', 'is_active', 'is_muted', 'formatted_last_read'
    ]
    list_filter = ['is_active', 'is_muted', RoleFilter, 'created_at']
    search_fields = ['user__email', 'thread__subject']
    autocomplete_fields = ['user', 'thread', 'role']
    readonly_fields = ['created_at', 'updated_at', 'last_read_at']
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('thread', 'user', 'role')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_muted', 'last_read_at')
        }),
        (_('Custom Permissions'), {
            'fields': ('custom_permissions',),
        }),
        (_('System Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_active', 'mark_as_inactive', 'mark_as_muted', 'mark_as_unmuted']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'thread', 'role'
        )

    def get_user_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    get_user_email.short_description = _('User')

    def get_thread_subject(self, obj):
        url = reverse('admin:auctions_messagethread_change', args=[obj.thread.id])
        return format_html('<a href="{}">{}</a>', url, obj.thread.subject)
    get_thread_subject.short_description = _('Thread')

    def get_role_name(self, obj):
        if obj.role:
            return obj.role.get_name_display()
        return _('No Role')
    get_role_name.short_description = _('Role')

    def formatted_last_read(self, obj):
        if obj.last_read_at:
            return obj.last_read_at.strftime('%Y-%m-%d %H:%M')
        return _('Never')
    formatted_last_read.short_description = _('Last Read')

    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _('%d participants marked as active.') % updated)
    mark_as_active.short_description = _('Mark selected participants as active')

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _('%d participants marked as inactive.') % updated)
    mark_as_inactive.short_description = _('Mark selected participants as inactive')

    def mark_as_muted(self, request, queryset):
        updated = queryset.update(is_muted=True)
        self.message_user(request, _('%d participants muted.') % updated)
    mark_as_muted.short_description = _('Mute selected participants')

    def mark_as_unmuted(self, request, queryset):
        updated = queryset.update(is_muted=False)
        self.message_user(request, _('%d participants unmuted.') % updated)
    mark_as_unmuted.short_description = _('Unmute selected participants')


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'thread_type', 'status', 'created_at', 'last_message_at']
    list_filter = ['thread_type', 'status', 'is_private', 'is_system_thread', 'created_at']
    search_fields = ['subject', 'creator__email', 'uuid']
    readonly_fields = ['uuid', 'created_at', 'updated_at', 'last_message_at']
    inlines = [ThreadParticipantInline, MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'thread', 'sender', 'message_type', 'status', 'sent_at', 'read_at']
    list_filter = ['message_type', 'status', 'is_system_message', 'is_important', 'sent_at']
    search_fields = ['content', 'sender__email', 'thread__subject']
    readonly_fields = ['sent_at', 'delivered_at', 'read_at', 'created_at', 'updated_at']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['property_number', 'title', 'property_type', 'city', 'status', 'owner', 'is_published']
    list_filter = ['property_type', 'status', 'city', 'is_featured', 'is_published', 'is_verified']
    search_fields = ['property_number', 'title', 'address', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ['title', 'related_property', 'auction_type', 'status', 'start_date', 'end_date']
    list_filter = ['auction_type', 'status', 'is_featured', 'is_published', 'is_private']
    search_fields = ['title', 'description', 'related_property__title']
    readonly_fields = ['uuid', 'created_at', 'updated_at']


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['auction', 'bidder', 'bid_amount', 'status', 'bid_time', 'is_auto_bid']
    list_filter = ['status', 'is_auto_bid', 'bid_time']
    search_fields = ['auction__title', 'bidder__email']
    readonly_fields = ['bid_time', 'created_at', 'updated_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['document_number', 'title', 'document_type', 'verification_status', 'uploaded_by']
    list_filter = ['document_type', 'verification_status', 'issue_date', 'expiry_date']
    search_fields = ['document_number', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'verification_date']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'title', 'related_property', 'status', 'buyer', 'seller']
    list_filter = ['status', 'contract_date', 'payment_method', 'is_verified']
    search_fields = ['contract_number', 'title', 'related_property__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'contract', 'payment_type', 'amount', 'payer', 'payee', 'status']
    list_filter = ['payment_type', 'status', 'payment_method', 'payment_date']
    search_fields = ['payment_number', 'transaction_reference', 'contract__contract_number']
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_number', 'transaction_type', 'amount', 'from_user', 'to_user', 'status']
    list_filter = ['transaction_type', 'status', 'transaction_date']
    search_fields = ['transaction_number', 'description', 'reference']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']


@admin.register(PropertyView)
class PropertyViewAdmin(admin.ModelAdmin):
    list_display = ['auction', 'view_type', 'location', 'size_sqm', 'elevation']
    list_filter = ['view_type']  # Removed created_at filter
    search_fields = ['location', 'address', 'legal_description']
    # Removed readonly_fields that reference created_at and updated_at


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'is_sent', 'sent_at']
    list_filter = ['notification_type', 'channel', 'is_read', 'is_sent']
    search_fields = ['title', 'content', 'recipient__email']
    readonly_fields = ['created_at', 'updated_at', 'read_at', 'sent_at']


admin.site.site_header = 'Auction'
admin.site.site_title = 'Auction'
admin.site.index_title = 'Auction'
