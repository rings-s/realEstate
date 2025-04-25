from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import json

from .models import (
    MessageThread, ThreadParticipant, Message, Property, Auction, Bid,
    Document, Contract, Notification, Media, RoleChoices
)
from .utils import sanitize_html, truncate_text




User = get_user_model()






# -------------------------------------------------------------------------
# Helper Serializers
# -------------------------------------------------------------------------

class UserBriefSerializer(serializers.ModelSerializer):
    """Brief serializer for User model used in nested relationships"""
    full_name = serializers.SerializerMethodField(label=_('Full Name'))
    primary_role = serializers.SerializerMethodField(label=_('Primary Role'))

    class Meta:
        model = User
        fields = [
            'id', 'uuid', 'email', 'full_name', 'primary_role',
            'avatar', 'phone_number'
        ]

    def get_full_name(self, obj):
        """Generate full name for user"""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email

    def get_primary_role(self, obj):
        """
        Get primary role for the user with proper error handling
        """
        try:
            # First check if the attribute exists
            if hasattr(obj, 'primary_role'):
                role_code = obj.primary_role or ''
                return {
                    'code': role_code,
                    'name': dict(RoleChoices.CHOICES).get(role_code, '')
                }

            # If not, try to get a role from related data
            elif hasattr(obj, 'has_role'):
                # Loop through known roles to find one the user has
                for role_code, role_name in RoleChoices.CHOICES:
                    if obj.has_role(role_code):
                        return {
                            'code': role_code,
                            'name': role_name
                        }

            # Default fallback
            return {
                'code': '',
                'name': ''
            }
        except Exception as e:
            # Log the error and return empty values
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting primary role: {str(e)}")
            return {
                'code': '',
                'name': ''
            }

class MediaSerializer(serializers.ModelSerializer):
    """
    Serializer for handling media uploads across different models.
    Provides URL generation and basic media information.
    """
    file_url = serializers.SerializerMethodField(label=_('File URL'))

    class Meta:
        model = Media
        fields = [
            'id',
            'name',
            'file',
            'file_url',
            'media_type',
            'uploaded_at'
        ]
        read_only_fields = ('file_url', 'media_type', 'uploaded_at')
        extra_kwargs = {
            'file': {'write_only': True},
            'name': {'required': False}
        }

    def get_file_url(self, obj):
        """
        Generate absolute URL for the media file.

        Args:
            obj: Media instance

        Returns:
            str: Absolute URL or None
        """
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

# -------------------------------------------------------------------------
# Base Serializers
# -------------------------------------------------------------------------


class BaseModelSerializer(serializers.ModelSerializer):
    """Base serializer with common fields for most models"""
    created_at = serializers.DateTimeField(
        read_only=True,
        format="%Y-%m-%d %H:%M:%S",
        label=_('Creation Date')
    )
    updated_at = serializers.DateTimeField(
        read_only=True,
        format="%Y-%m-%d %H:%M:%S",
        label=_('Last Updated')
    )

    def to_internal_value(self, data):
        """
        Handle JSON fields and sanitize text fields
        """
        # Identify JSON and text fields in the model
        json_fields = [
            field.name for field in self.Meta.model._meta.fields
            if isinstance(field, models.JSONField)
        ]
        text_fields = [
            field.name for field in self.Meta.model._meta.fields
            if isinstance(field, models.TextField)
        ]

        # Process JSON fields
        for field in json_fields:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    data[field] = {} if field in ['metadata', 'location'] else []

        # Sanitize text fields
        for field in text_fields:
            if field in data and isinstance(data[field], str):
                data[field] = sanitize_html(data[field])

        return super().to_internal_value(data)

    def to_representation(self, instance):
        """
        Ensure JSON fields are properly serialized
        """
        representation = super().to_representation(instance)

        # Identify JSON fields
        json_fields = [
            field.name for field in self.Meta.model._meta.fields
            if isinstance(field, models.JSONField)
        ]

        # Ensure JSON fields are properly formatted
        for field in json_fields:
            value = representation.get(field)
            if value is None:
                representation[field] = {} if field in ['metadata', 'location'] else []
            elif isinstance(value, str):
                try:
                    representation[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    representation[field] = {} if field in ['metadata', 'location'] else []

        return representation

    def create(self, validated_data):
        """
        Custom create method to handle nested data
        """
        # Remove nested serializer data
        nested_fields = [
            field for field, serializer in self.fields.items()
            if isinstance(serializer, serializers.BaseSerializer)
        ]
        for field in nested_fields:
            validated_data.pop(field, None)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Custom update method to handle nested data
        """
        # Remove nested serializer data
        nested_fields = [
            field for field, serializer in self.fields.items()
            if isinstance(serializer, serializers.BaseSerializer)
        ]
        for field in nested_fields:
            validated_data.pop(field, None)

        return super().update(instance, validated_data)


# -------------------------------------------------------------------------
# Message & Thread Serializers
# -------------------------------------------------------------------------




class MessageSerializer(BaseModelSerializer):
    """Serializer for Message model"""
    sender_details = UserBriefSerializer(source='sender', read_only=True, label=_('تفاصيل المرسل'))
    reply_to_details = serializers.SerializerMethodField(label=_('تفاصيل الرد على'))
    media = MediaSerializer(many=True, read_only=True, label=_('المرفقات'))

    class Meta:
        model = Message
        fields = [
            'id', 'thread', 'sender', 'sender_details', 'content', 'message_type',
            'status',
            'media',
            'reply_to', 'reply_to_details', 'sent_at', 'delivered_at', 'read_at',
            'is_system_message', 'is_important', 'metadata', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'sender': {'write_only': True},
            'thread': {'write_only': True},
            'reply_to': {'write_only': True},
            'sent_at': {'read_only': True, 'label': _('وقت الإرسال')},
            'delivered_at': {'read_only': True, 'label': _('وقت التسليم')},
            'read_at': {'read_only': True, 'label': _('وقت القراءة')},
            'content': {'label': _('المحتوى')},
            'message_type': {'label': _('نوع الرسالة')},
            'status': {'label': _('الحالة')},
            'media': {'label': _('المرفقات')},
            'is_system_message': {'label': _('رسالة نظام')},
            'is_important': {'label': _('مهمة')},
            'metadata': {'label': _('بيانات وصفية')},
        }

    def get_reply_to_details(self, obj):
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'content': obj.reply_to.content[:100] + '...' if len(obj.reply_to.content) > 100 else obj.reply_to.content,
                'sender': {
                    'id': obj.reply_to.sender.id,
                    'name': obj.reply_to.sender.get_full_name() or obj.reply_to.sender.email if obj.reply_to.sender else _('مستخدم محذوف')
                } if obj.reply_to.sender else None,
                'sent_at': obj.reply_to.sent_at
            }
        return None

    def validate(self, data):
        # Ensure content or associated media (on create) is provided
        # Note: Validating media presence on create is tricky here as it's read_only.
        # This validation might need to happen in the view or via a separate upload step.
        # For now, just check for content.
        if not data.get('content'):
             # If we enhance this serializer for writes later, we'd check for media here too.
             pass # Allow messages with only attachments (handled separately)
            # raise serializers.ValidationError(_('يجب توفير محتوى للرسالة'))
        return data


class ThreadParticipantSerializer(BaseModelSerializer):
    """Serializer for ThreadParticipant model"""
    user_details = UserBriefSerializer(source='user', read_only=True, label=_('تفاصيل المستخدم'))
    role_details = serializers.SerializerMethodField(label=_('تفاصيل الدور'))

    class Meta:
        model = ThreadParticipant
        fields = [
            'id', 'thread', 'user', 'user_details', 'role', 'role_details',
            'is_active', 'is_muted', 'last_read_at', 'custom_permissions',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'user': {'write_only': True},
            'thread': {'write_only': True},
            'role': {'write_only': True},
            'is_active': {'label': _('نشط')},
            'is_muted': {'label': _('صامت')},
            'last_read_at': {'label': _('آخر قراءة')},
            'custom_permissions': {'label': _('صلاحيات مخصصة')},
        }

    def get_role_details(self, obj):
        if obj.role:
            return {
                'id': obj.role.id,
                'name': obj.role.name,
                'display_name': obj.role.get_name_display() if hasattr(obj.role, 'get_name_display') else obj.role.name
            }
        return None


class MessageThreadSerializer(BaseModelSerializer):
    """Serializer for MessageThread model"""
    participants = ThreadParticipantSerializer(many=True, read_only=True, label=_('المشاركون'))
    messages_count = serializers.SerializerMethodField(label=_('عدد الرسائل'))
    latest_message = serializers.SerializerMethodField(label=_('أحدث رسالة'))
    creator_details = UserBriefSerializer(source='creator', read_only=True, label=_('تفاصيل المنشئ'))

    class Meta:
        model = MessageThread
        fields = [
            'id', 'uuid', 'subject', 'thread_type', 'status', 'creator', 'creator_details',
            'related_property', 'related_auction', 'is_private', 'is_system_thread',
            'last_message_at', 'participants', 'messages_count', 'latest_message',
            'metadata', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'uuid': {'read_only': True, 'label': _('معرف فريد')},
            'creator': {'write_only': True},
            'last_message_at': {'read_only': True, 'label': _('وقت آخر رسالة')},
            'subject': {'label': _('الموضوع')},
            'thread_type': {'label': _('نوع المحادثة')},
            'status': {'label': _('الحالة')},
            'related_property': {'label': _('العقار المرتبط')},
            'related_auction': {'label': _('المزاد المرتبط')},
            'is_private': {'label': _('محادثة خاصة')},
            'is_system_thread': {'label': _('محادثة نظام')},
            'metadata': {'label': _('بيانات إضافية')},
        }

    def get_messages_count(self, obj):
        return obj.messages.count()

    def get_latest_message(self, obj):
        latest = obj.messages.order_by('-sent_at').first()
        if latest:
            return {
                'id': latest.id,
                'content': latest.content[:100] + '...' if len(latest.content) > 100 else latest.content,
                'sender': {
                    'id': latest.sender.id,
                    'name': latest.sender.get_full_name() or latest.sender.email
                } if latest.sender else None,
                'sent_at': latest.sent_at,
                'message_type': latest.message_type
            }
        return None

    def create(self, validated_data):
        # Create thread
        thread = MessageThread.objects.create(**validated_data)

        # Add creator as participant if creator is provided
        if 'creator' in validated_data and validated_data['creator']:
            creator = validated_data['creator']
            # Get default role for creator (assuming admin/owner role exists)
            try:
                owner_role = Role.objects.get(name='owner')
            except Role.DoesNotExist:
                owner_role = None

            ThreadParticipant.objects.create(
                thread=thread,
                user=creator,
                role=owner_role,
                is_active=True
            )

        return thread



# -------------------------------------------------------------------------
# Property Serializers
# -------------------------------------------------------------------------


class PropertySerializer(BaseModelSerializer):
    """Serializer for Property model"""
    media = MediaSerializer(many=True, read_only=True, label=_('ملفات الوسائط'))
    owner_details = UserBriefSerializer(source='owner', read_only=True, label=_('تفاصيل المالك'))
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True, label=_('نوع العقار المعروض'))
    status_display = serializers.CharField(source='get_status_display', read_only=True, label=_('الحالة المعروضة'))

    class Meta:
        model = Property
        fields = [
            'id', 'property_number', 'title', 'property_type', 'property_type_display',
            'status', 'status_display', 'location', 'address', 'city', 'state',
            'postal_code', 'country', 'description', 'features', 'amenities',
            'rooms', 'specifications', 'size_sqm', 'bedrooms', 'bathrooms',
            'floors', 'parking_spaces', 'year_built', 'market_value', 'minimum_bid',
            'pricing_details', 'owner', 'owner_details', 'is_published',
            'is_featured', 'is_verified', 'slug',
            'media',
            'metadata', 'created_at', 'updated_at',
            'deed_number', 'highQualityStreets'
        ]
        extra_kwargs = {
            'owner': {'write_only': True, 'label': _('المالك')},
            'property_number': {'read_only': True, 'label': _('رقم العقار')},
            'slug': {'read_only': True, 'label': _('الرابط المختصر')},
            'deed_number': {'label': _('رقم الصك')},
            'highQualityStreets': {'label': _('الشوارع الراقية')},
            'floors': {'label': _('عدد الطوابق')},
            'media': {'label': _('ملفات الوسائط')},
        }

    def validate_location(self, value):
        """Validate location data."""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError(_("يجب أن تكون بيانات الموقع على شكل قاموس."))
        return value

    def to_internal_value(self, data):
        """
        Handle JSON fields properly before validation
        """
        # Handle JSON fields if they come as strings
        json_fields = ['features', 'amenities', 'rooms', 'specifications', 'location', 'pricing_details', 'metadata', 'highQualityStreets']

        data_copy = data.copy()
        for field in json_fields:
            if field in data_copy and isinstance(data_copy[field], str):
                try:
                    # Try to parse if it's a JSON string
                    data_copy[field] = json.loads(data_copy[field])
                except (json.JSONDecodeError, ValueError):
                    # If it's not valid JSON, handle appropriately
                    if field in ['features', 'amenities', 'rooms', 'highQualityStreets']:
                        # For array fields
                        data_copy[field] = []
                    else:
                        # For object fields
                        data_copy[field] = {}

        return super().to_internal_value(data_copy)

    def to_representation(self, instance):
        """
        Ensure JSON fields are properly serialized
        """
        representation = super().to_representation(instance)

        # Ensure array fields are properly serialized
        array_fields = ['features', 'amenities', 'rooms', 'highQualityStreets']
        for field in array_fields:
            value = representation.get(field)
            if value is None:
                representation[field] = []
            elif isinstance(value, str):
                try:
                    representation[field] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    representation[field] = []

        # Ensure object fields are properly serialized
        object_fields = ['specifications', 'location', 'pricing_details', 'metadata']
        for field in object_fields:
            value = representation.get(field)
            if value is None:
                representation[field] = {}
            elif isinstance(value, str):
                try:
                    representation[field] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    representation[field] = {}

        return representation


# -------------------------------------------------------------------------
# Bid Serializer
# -------------------------------------------------------------------------

class BidSerializer(BaseModelSerializer):
    """Serializer for Bid model"""
    bidder_details = UserBriefSerializer(source='bidder', read_only=True, label=_('تفاصيل المزايد'))
    auction_details = serializers.SerializerMethodField(label=_('تفاصيل المزاد'))
    status_display = serializers.CharField(source='get_status_display', read_only=True, label=_('الحالة المعروضة'))

    class Meta:
        model = Bid
        fields = [
            'id', 'auction', 'auction_details', 'bidder', 'bidder_details',
            'bid_amount', 'bid_time', 'status', 'status_display', 'is_auto_bid',
            'max_auto_bid', 'ip_address', 'user_agent', 'notes', 'metadata',
            'payment_info', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'auction': {'write_only': True, 'label': _('المزاد')},
            'bidder': {'write_only': True, 'label': _('المزايد')},
            'bid_time': {'read_only': True, 'label': _('وقت المزايدة')},
            'ip_address': {'read_only': True, 'label': _('عنوان IP')},
            'user_agent': {'read_only': True, 'label': _('وكيل المستخدم')},
            'bid_amount': {'label': _('مبلغ المزايدة')},
            'status': {'label': _('الحالة')},
            'is_auto_bid': {'label': _('مزايدة تلقائية')},
            'max_auto_bid': {'label': _('الحد الأقصى للمزايدة التلقائية')},
            'notes': {'label': _('ملاحظات')},
            'metadata': {'label': _('بيانات إضافية')},
            'payment_info': {'label': _('معلومات الدفع')},
        }

    def get_auction_details(self, obj):
        if obj.auction:
            return {
                'id': obj.auction.id,
                'title': obj.auction.title,
                'current_bid': obj.auction.current_bid,
                'status': obj.auction.status,
                'end_date': obj.auction.end_date
            }
        return None

    def validate(self, data):
        # Validate bid amount is greater than auction minimum increment
        auction = data.get('auction')
        bid_amount = data.get('bid_amount')

        if auction and bid_amount:
            # For a new bid
            if not self.instance:
                if auction.current_bid and bid_amount <= auction.current_bid:
                    raise serializers.ValidationError(_("مبلغ المزايدة يجب أن يكون أكبر من المزايدة الحالية."))

                if auction.starting_bid and bid_amount < auction.starting_bid:
                    raise serializers.ValidationError(_("مبلغ المزايدة يجب أن لا يقل عن المزايدة الأولية."))

                # Check minimum increment
                if auction.current_bid and auction.minimum_increment:
                    min_valid_bid = auction.current_bid + auction.minimum_increment
                    if bid_amount < min_valid_bid:
                        raise serializers.ValidationError(
                            _("مبلغ المزايدة يجب أن يكون أكبر من المزايدة الحالية بالإضافة إلى الحد الأدنى للزيادة ({}).").format(
                                auction.minimum_increment
                            )
                        )

        # Validate auto bid
        if data.get('is_auto_bid') and not data.get('max_auto_bid'):
            raise serializers.ValidationError(_("يجب تحديد الحد الأقصى للمزايدة التلقائية."))

        return data


# -------------------------------------------------------------------------
# Auction Serializer
# -------------------------------------------------------------------------

class AuctionSerializer(BaseModelSerializer):
    """Serializer for Auction model"""
    media = MediaSerializer(many=True, read_only=True, label=_('ملفات الوسائط'))
    property_details = serializers.SerializerMethodField(label=_('تفاصيل العقار'))
    auction_type_display = serializers.CharField(source='get_auction_type_display', read_only=True, label=_('نوع المزاد المعروض'))
    status_display = serializers.CharField(source='get_status_display', read_only=True, label=_('الحالة المعروضة'))
    highest_bid = serializers.SerializerMethodField(label=_('أعلى مزايدة'))
    bids_count = serializers.SerializerMethodField(label=_('عدد المزايدات'))
    time_remaining = serializers.SerializerMethodField(label=_('الوقت المتبقي'))

    class Meta:
        model = Auction
        fields = [
            'id', 'slug', 'title', 'auction_type', 'auction_type_display',
            'status', 'status_display', 'description', 'start_date', 'end_date',
            'registration_deadline', 'viewing_dates', 'timeline', 'related_property',
            'property_details', 'starting_bid', 'reserve_price', 'minimum_increment',
            'current_bid', 'estimated_value', 'bid_history', 'financial_terms',
            'buyer_premium_percent', 'registration_fee', 'deposit_required',
            'is_published', 'is_featured', 'is_private',
            'media',
            'terms_conditions', 'special_notes', 'view_count',
            'bid_count', 'registered_bidders', 'analytics', 'highest_bid',
            'bids_count', 'time_remaining',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'slug': {'read_only': True, 'label': _('الرابط المختصر')},
            'current_bid': {'read_only': True, 'label': _('المزايدة الحالية')},
            'bid_history': {'read_only': True, 'label': _('سجل المزايدات')},
            'view_count': {'read_only': True, 'label': _('عدد المشاهدات')},
            'bid_count': {'read_only': True, 'label': _('عدد المزايدات')},
            'registered_bidders': {'read_only': True, 'label': _('المزايدين المسجلين')},
            'title': {'label': _('العنوان')},
            'auction_type': {'label': _('نوع المزاد')},
            'status': {'label': _('الحالة')},
            'description': {'label': _('الوصف')},
            'start_date': {'label': _('تاريخ البدء')},
            'end_date': {'label': _('تاريخ الانتهاء')},
            'registration_deadline': {'label': _('موعد انتهاء التسجيل')},
            'viewing_dates': {'label': _('مواعيد المعاينة')},
            'timeline': {'label': _('الجدول الزمني')},
            'related_property': {'label': _('العقار المرتبط')},
            'starting_bid': {'label': _('المزايدة الأولية')},
            'reserve_price': {'label': _('السعر المحفوظ')},
            'minimum_increment': {'label': _('الحد الأدنى للزيادة')},
            'estimated_value': {'label': _('القيمة التقديرية')},
            'financial_terms': {'label': _('الشروط المالية')},
            'buyer_premium_percent': {'label': _('عمولة المشتري (%)')},
            'registration_fee': {'label': _('رسوم التسجيل')},
            'deposit_required': {'label': _('التأمين المطلوب')},
            'is_published': {'label': _('منشور')},
            'is_featured': {'label': _('مميز')},
            'is_private': {'label': _('مزاد خاص')},
            'media': {'label': _('ملفات الوسائط')},
            'terms_conditions': {'label': _('الشروط والأحكام')},
            'special_notes': {'label': _('ملاحظات خاصة')},
            'analytics': {'label': _('بيانات تحليلية')},
        }

    def get_property_details(self, obj):
        if obj.related_property:
            property_media = obj.related_property.media.filter(media_type='image').first()
            property_cover_url = None
            request = self.context.get('request')
            if property_media and property_media.file:
                if request:
                    property_cover_url = request.build_absolute_uri(property_media.file.url)
                else:
                    property_cover_url = property_media.file.url

            return {
                'id': obj.related_property.id,
                'title': obj.related_property.title,
                'property_type': obj.related_property.property_type,
                'property_type_display': obj.related_property.get_property_type_display(),
                'address': obj.related_property.address,
                'city': obj.related_property.city,
                'cover_image_url': property_cover_url,
                'size_sqm': obj.related_property.size_sqm,
                'bedrooms': obj.related_property.bedrooms,
                'bathrooms': obj.related_property.bathrooms,
            }
        return None

    def get_highest_bid(self, obj):
        highest_bid = obj.bids.filter(status__in=['accepted', 'winning']).order_by('-bid_amount').first()
        if highest_bid:
            return {
                'id': highest_bid.id,
                'amount': highest_bid.bid_amount,
                'bidder': {
                    'id': highest_bid.bidder.id,
                    'name': highest_bid.bidder.get_full_name() or highest_bid.bidder.email
                },
                'time': highest_bid.bid_time
            }
        return None

    def get_bids_count(self, obj):
        return obj.bids.count()

    def get_time_remaining(self, obj):
        from django.utils import timezone
        import datetime

        if obj.end_date > timezone.now():
            time_left = obj.end_date - timezone.now()
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            return {
                'days': days,
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds,
                'total_seconds': time_left.total_seconds()
            }
        return {
            'days': 0,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
            'total_seconds': 0
        }
# -------------------------------------------------------------------------
# Document Serializers
# -------------------------------------------------------------------------

class DocumentSerializer(BaseModelSerializer):
    """Serializer for Document model"""
    uploaded_by_details = UserBriefSerializer(source='uploaded_by', read_only=True, label=_('تفاصيل الناشر'))
    verified_by_details = UserBriefSerializer(source='verified_by', read_only=True, label=_('تم التحقق بواسطة'))
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True, label=_('نوع الوثيقة المعروض'))
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True, label=_('حالة التحقق المعروضة'))
    media = MediaSerializer(many=True, read_only=True, label=_('ملفات الوسائط'))

    class Meta:
        model = Document
        fields = [
            'id', 'document_number', 'title', 'document_type', 'document_type_display',
            'description',
            'media',
            'verification_status', 'verification_status_display', 'verification_date',
            'verification_notes', 'verification_details', 'issue_date', 'expiry_date',
            'related_property', 'related_auction', 'related_contract', 'uploaded_by',
            'uploaded_by_details', 'verified_by', 'verified_by_details',
            'document_metadata', 'is_public',
            'access_code', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'document_number': {'read_only': True, 'label': _('رقم الوثيقة')},
            'uploaded_by': {'write_only': True, 'label': _('تم التحميل بواسطة')},
            'verified_by': {'write_only': True, 'label': _('تم التحقق بواسطة')},
            'verification_date': {'read_only': True, 'label': _('تاريخ التحقق')},
            'title': {'label': _('العنوان')},
            'document_type': {'label': _('نوع الوثيقة')},
            'description': {'label': _('الوصف')},
            'media': {'label': _('ملفات الوسائط')},
            'verification_status': {'label': _('حالة التحقق')},
            'verification_notes': {'label': _('ملاحظات التحقق')},
            'verification_details': {'label': _('تفاصيل التحقق')},
            'issue_date': {'label': _('تاريخ الإصدار')},
            'expiry_date': {'label': _('تاريخ الانتهاء')},
            'related_property': {'label': _('العقار المرتبط')},
            'related_auction': {'label': _('المزاد المرتبط')},
            'related_contract': {'label': _('العقد المرتبط')},
            'document_metadata': {'label': _('بيانات وصفية للوثيقة')},
            'is_public': {'label': _('عامة')},
            'access_code': {'label': _('رمز الوصول')},
        }


# -------------------------------------------------------------------------
# Contract Serializers
# -------------------------------------------------------------------------

class ContractSerializer(BaseModelSerializer):
    """Serializer for Contract model"""
    property_details = serializers.SerializerMethodField(label=_('تفاصيل العقار'))
    auction_details = serializers.SerializerMethodField(label=_('تفاصيل المزاد'))
    buyer_details = UserBriefSerializer(source='buyer', read_only=True, label=_('تفاصيل المشتري'))
    seller_details = UserBriefSerializer(source='seller', read_only=True, label=_('تفاصيل البائع'))
    verified_by_details = UserBriefSerializer(source='verified_by', read_only=True, label=_('تم التحقق بواسطة'))
    status_display = serializers.CharField(source='get_status_display', read_only=True, label=_('الحالة المعروضة'))
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True, label=_('طريقة الدفع المعروضة'))
    documents = DocumentSerializer(many=True, read_only=True, label=_('الوثائق'))
    media = MediaSerializer(many=True, read_only=True, label=_('ملفات العقد'))

    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'title', 'description', 'status', 'status_display',
            'media',
            'related_property', 'property_details',
            'related_auction', 'auction_details', 'buyer', 'buyer_details',
            'seller', 'seller_details', 'contract_date', 'effective_date',
            'expiry_date', 'timeline', 'total_amount', 'down_payment',
            'payment_method', 'payment_method_display', 'payment_terms',
            'payment_details', 'payments_history', 'special_conditions',
            'is_verified', 'verified_by', 'verified_by_details', 'verification_date',
            'buyer_signed', 'buyer_signed_date', 'seller_signed', 'seller_signed_date',
            'parties', 'documents', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'contract_number': {'read_only': True, 'label': _('رقم العقد')},
            'buyer': {'write_only': True, 'label': _('المشتري')},
            'seller': {'write_only': True, 'label': _('البائع')},
            'verified_by': {'write_only': True, 'label': _('تم التحقق بواسطة')},
            'verification_date': {'read_only': True, 'label': _('تاريخ التحقق')},
            'buyer_signed_date': {'read_only': True, 'label': _('تاريخ توقيع المشتري')},
            'seller_signed_date': {'read_only': True, 'label': _('تاريخ توقيع البائع')},
            'title': {'label': _('العنوان')},
            'description': {'label': _('الوصف')},
            'status': {'label': _('الحالة')},
            'media': {'label': _('ملفات العقد')},
            'related_property': {'label': _('العقار المرتبط')},
            'related_auction': {'label': _('المزاد المرتبط')},
            'contract_date': {'label': _('تاريخ العقد')},
            'effective_date': {'label': _('تاريخ السريان')},
            'expiry_date': {'label': _('تاريخ الانتهاء')},
            'timeline': {'label': _('الجدول الزمني')},
            'total_amount': {'label': _('المبلغ الإجمالي')},
            'down_payment': {'label': _('الدفعة الأولى')},
            'payment_method': {'label': _('طريقة الدفع')},
            'payment_terms': {'label': _('شروط الدفع')},
            'payment_details': {'label': _('تفاصيل الدفع')},
            'payments_history': {'label': _('سجل المدفوعات')},
            'special_conditions': {'label': _('شروط خاصة')},
            'is_verified': {'label': _('تم التحقق')},
            'buyer_signed': {'label': _('توقيع المشتري')},
            'seller_signed': {'label': _('توقيع البائع')},
            'parties': {'label': _('الأطراف')},
        }

    def get_property_details(self, obj):
        if obj.related_property:
            return {
                'id': obj.related_property.id,
                'title': obj.related_property.title,
                'property_type': obj.related_property.property_type,
                'property_type_display': obj.related_property.get_property_type_display(),
                'address': obj.related_property.address,
                'city': obj.related_property.city,
            }
        return None

    def get_auction_details(self, obj):
        if obj.related_auction:
            return {
                'id': obj.related_auction.id,
                'title': obj.related_auction.title,
                'final_bid': obj.related_auction.current_bid,
            }
        return None

    def validate(self, data):
        # Ensure buyer and seller are different users
        buyer = data.get('buyer')
        seller = data.get('seller')
        if buyer and seller and buyer == seller:
            raise serializers.ValidationError(_("لا يمكن أن يكون المشتري والبائع نفس المستخدم."))

        # Validate dates
        contract_date = data.get('contract_date')
        effective_date = data.get('effective_date')
        expiry_date = data.get('expiry_date')

        if effective_date and contract_date and effective_date < contract_date:
            raise serializers.ValidationError(_("تاريخ السريان يجب أن يكون بعد أو يساوي تاريخ العقد."))

        if expiry_date and effective_date and expiry_date < effective_date:
            raise serializers.ValidationError(_("تاريخ الانتهاء يجب أن يكون بعد تاريخ السريان."))

        return data


# -------------------------------------------------------------------------
# Notification Serializers
# -------------------------------------------------------------------------

class NotificationSerializer(BaseModelSerializer):
    """Serializer for Notification model"""
    recipient_details = UserBriefSerializer(source='recipient', read_only=True, label=_('تفاصيل المستلم'))
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True, label=_('نوع الإشعار المعروض'))
    channel_display = serializers.CharField(source='get_channel_display', read_only=True, label=_('القناة المعروضة'))

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_details', 'notification_type',
            'notification_type_display', 'title', 'content', 'channel',
            'channel_display', 'is_read', 'read_at', 'is_sent', 'sent_at',
            'related_thread', 'related_auction', 'related_property',
            'related_contract', 'action_url', 'is_important', 'expiry_date',
            'notification_data', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'recipient': {'write_only': True, 'label': _('المستلم')},
            'read_at': {'read_only': True, 'label': _('وقت القراءة')},
            'sent_at': {'read_only': True, 'label': _('وقت الإرسال')},
            'notification_type': {'label': _('نوع الإشعار')},
            'title': {'label': _('العنوان')},
            'content': {'label': _('المحتوى')},
            'channel': {'label': _('القناة')},
            'is_read': {'label': _('مقروءة')},
            'is_sent': {'label': _('تم الإرسال')},
            'related_thread': {'label': _('المحادثة المرتبطة')},
            'related_auction': {'label': _('المزاد المرتبط')},
            'related_property': {'label': _('العقار المرتبط')},
            'related_contract': {'label': _('العقد المرتبط')},
            'action_url': {'label': _('رابط الإجراء')},
            'is_important': {'label': _('مهم')},
            'expiry_date': {'label': _('تاريخ انتهاء الصلاحية')},
            'notification_data': {'label': _('بيانات الإشعار')},
        }

    def validate(self, data):
        # Ensure at least one related entity is provided for certain notification types
        notification_type = data.get('notification_type')
        related_thread = data.get('related_thread')
        related_auction = data.get('related_auction')
        related_property = data.get('related_property')
        related_contract = data.get('related_contract')

        if notification_type in ['auction_start', 'auction_end', 'outbid', 'bid_success', 'auction_won'] and not related_auction:
            raise serializers.ValidationError(_("يجب تحديد المزاد المرتبط لهذا النوع من الإشعارات."))

        if notification_type == 'message' and not related_thread:
            raise serializers.ValidationError(_("يجب تحديد المحادثة المرتبطة لإشعارات الرسائل."))

        if notification_type in ['payment_due', 'payment_received'] and not related_contract:
            raise serializers.ValidationError(_("يجب تحديد العقد المرتبط لإشعارات الدفع."))

        return data



class JSONSerializerField(serializers.Field):
    """
    Custom serializer field for handling JSON data with type inference and validation.
    """
    def to_representation(self, value):
        """
        Convert JSON data to representation.

        Args:
            value: JSON data

        Returns:
            Dict or list
        """
        if value is None:
            return {} if isinstance(value, dict) else []
        return value

    def to_internal_value(self, data):
        """
        Validate and convert input data to JSON.

        Args:
            data: Input data

        Returns:
            Dict or list
        """
        if isinstance(data, str):
            try:
                import json
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                raise serializers.ValidationError(_("Invalid JSON format"))
        return data
