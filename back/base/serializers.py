from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import (
    MessageThread, ThreadParticipant, Message, Property, PropertyImage,
    PropertyView, Auction, AuctionImage, Bid, Document, Contract, Notification
)
from accounts.models import Role
from accounts.serializers import (
    RoleSerializer, UserProfileSerializer
)

User = get_user_model()


# -------------------------------------------------------------------------
# Helper Serializers
# -------------------------------------------------------------------------

class UserBriefSerializer(serializers.ModelSerializer):
    """Brief serializer for User model used in nested relationships"""
    full_name = serializers.SerializerMethodField(label=_('الإسم الكامل'))
    primary_role = serializers.SerializerMethodField(label=_('الدور الأساسي'))

    class Meta:
        model = User
        fields = [
            'id', 'uuid', 'email', 'full_name', 'primary_role', 'avatar', 'phone_number'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email

    def get_primary_role(self, obj):
        primary_role = obj.primary_role
        if primary_role:
            role_obj = next((r for r in obj.roles.all() if r.name == primary_role), None)
            if role_obj:
                return {
                    'code': role_obj.name,
                    'name': role_obj.get_name_display()
                }
        return None


# -------------------------------------------------------------------------
# Base Serializers
# -------------------------------------------------------------------------

class BaseModelSerializer(serializers.ModelSerializer):
    """Base serializer with common fields for most models"""
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S", label=_('تاريخ الإنشاء'))
    updated_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S", label=_('تاريخ التحديث'))


# -------------------------------------------------------------------------
# Message & Thread Serializers
# -------------------------------------------------------------------------

class MessageSerializer(BaseModelSerializer):
    """Serializer for Message model"""
    sender_details = UserBriefSerializer(source='sender', read_only=True, label=_('تفاصيل المرسل'))
    reply_to_details = serializers.SerializerMethodField(label=_('تفاصيل الرد على'))

    class Meta:
        model = Message
        fields = [
            'id', 'thread', 'sender', 'sender_details', 'content', 'message_type',
            'status', 'attachment', 'attachment_type', 'attachment_name', 'attachment_size',
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
            'attachment': {'label': _('المرفق')},
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
        # Ensure content or attachment is provided
        if not data.get('content') and not data.get('attachment'):
            raise serializers.ValidationError(_('يجب توفير محتوى أو مرفق للرسالة'))
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

class PropertyImageSerializer(BaseModelSerializer):
    """Serializer for PropertyImage model"""
    image_url = serializers.SerializerMethodField(label=_('رابط الصورة'))
    property_title = serializers.SerializerMethodField(label=_('عنوان العقار'))

    class Meta:
        model = PropertyImage
        fields = [
            'id', 'property', 'property_title', 'image', 'image_url', 'is_primary',
            'caption', 'alt_text', 'order', 'width', 'height', 'file_size',
            'metadata', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'property': {'write_only': True, 'label': _('العقار')},
            'width': {'read_only': True, 'label': _('العرض')},
            'height': {'read_only': True, 'label': _('الارتفاع')},
            'file_size': {'read_only': True, 'label': _('حجم الملف (كيلوبايت)')},
            'image': {'label': _('الصورة')},
            'is_primary': {'label': _('صورة رئيسية')},
            'caption': {'label': _('التعليق')},
            'alt_text': {'label': _('النص البديل')},
            'order': {'label': _('ترتيب العرض')},
            'metadata': {'label': _('بيانات وصفية')},
        }

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_property_title(self, obj):
        return obj.property.title if obj.property else None


class PropertySerializer(BaseModelSerializer):
    """Serializer for Property model"""
    images = PropertyImageSerializer(many=True, read_only=True, label=_('الصور'))
    cover_image_url = serializers.SerializerMethodField(label=_('رابط صورة الغلاف'))
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
            'parking_spaces', 'year_built', 'market_value', 'minimum_bid',
            'pricing_details', 'owner', 'owner_details', 'is_published',
            'is_featured', 'is_verified', 'slug', 'meta_title', 'meta_description',
            'cover_image', 'cover_image_url', 'images', 'metadata', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'owner': {'write_only': True, 'label': _('المالك')},
            'property_number': {'read_only': True, 'label': _('رقم العقار')},
            'slug': {'read_only': True, 'label': _('الرابط المختصر')},
            'title': {'label': _('العنوان')},
            'property_type': {'label': _('نوع العقار')},
            'status': {'label': _('الحالة')},
            'location': {'label': _('الموقع الجغرافي')},
            'address': {'label': _('العنوان')},
            'city': {'label': _('المدينة')},
            'state': {'label': _('المنطقة/المحافظة')},
            'postal_code': {'label': _('الرمز البريدي')},
            'country': {'label': _('الدولة')},
            'description': {'label': _('الوصف')},
            'features': {'label': _('المميزات')},
            'amenities': {'label': _('المرافق')},
            'rooms': {'label': _('الغرف')},
            'specifications': {'label': _('المواصفات')},
            'size_sqm': {'label': _('المساحة (متر مربع)')},
            'bedrooms': {'label': _('عدد غرف النوم')},
            'bathrooms': {'label': _('عدد الحمامات')},
            'parking_spaces': {'label': _('أماكن وقوف السيارات')},
            'year_built': {'label': _('سنة البناء')},
            'market_value': {'label': _('القيمة السوقية')},
            'minimum_bid': {'label': _('الحد الأدنى للمزايدة')},
            'pricing_details': {'label': _('تفاصيل التسعير')},
            'is_published': {'label': _('منشور')},
            'is_featured': {'label': _('مميز')},
            'is_verified': {'label': _('موثق')},
            'meta_title': {'label': _('عنوان الميتا')},
            'meta_description': {'label': _('وصف الميتا')},
            'cover_image': {'label': _('صورة الغلاف')},
            'metadata': {'label': _('بيانات إضافية')},
        }

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def validate_location(self, value):
        """Validate location data."""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError(_("يجب أن تكون بيانات الموقع على شكل قاموس."))
        return value


class PropertyViewSerializer(BaseModelSerializer):
    """Serializer for PropertyView model"""
    view_type_display = serializers.CharField(source='get_view_type_display', read_only=True, label=_('نوع العرض المعروض'))
    auction_title = serializers.SerializerMethodField(label=_('عنوان المزاد'))
    image_url = serializers.SerializerMethodField(label=_('رابط الصورة'))
    file_url = serializers.SerializerMethodField(label=_('رابط الملف'))

    class Meta:
        model = PropertyView
        fields = [
            'id', 'auction', 'auction_title', 'view_type', 'view_type_display',
            'location', 'dimensions', 'address', 'legal_description', 'size_sqm',
            'elevation', 'image', 'image_url', 'file', 'file_url', 'external_url',
            'embed_code', 'view_config', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'auction': {'write_only': True, 'label': _('المزاد')},
            'view_type': {'label': _('نوع العرض')},
            'location': {'label': _('الموقع')},
            'dimensions': {'label': _('الأبعاد')},
            'address': {'label': _('العنوان')},
            'legal_description': {'label': _('الوصف القانوني')},
            'size_sqm': {'label': _('المساحة (متر مربع)')},
            'elevation': {'label': _('الارتفاع')},
            'image': {'label': _('الصورة')},
            'file': {'label': _('الملف')},
            'external_url': {'label': _('رابط خارجي')},
            'embed_code': {'label': _('كود التضمين')},
            'view_config': {'label': _('إعدادات العرض')},
        }

    def get_auction_title(self, obj):
        return obj.auction.title if obj.auction else None

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


# -------------------------------------------------------------------------
# Auction Serializers
# -------------------------------------------------------------------------

class AuctionImageSerializer(BaseModelSerializer):
    """Serializer for AuctionImage model"""
    image_url = serializers.SerializerMethodField(label=_('رابط الصورة'))
    auction_title = serializers.SerializerMethodField(label=_('عنوان المزاد'))

    class Meta:
        model = AuctionImage
        fields = [
            'id', 'auction', 'auction_title', 'image', 'image_url', 'is_primary',
            'caption', 'alt_text', 'order', 'width', 'height', 'file_size',
            'metadata', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'auction': {'write_only': True, 'label': _('المزاد')},
            'width': {'read_only': True, 'label': _('العرض')},
            'height': {'read_only': True, 'label': _('الارتفاع')},
            'file_size': {'read_only': True, 'label': _('حجم الملف (كيلوبايت)')},
            'image': {'label': _('الصورة')},
            'is_primary': {'label': _('صورة رئيسية')},
            'caption': {'label': _('التعليق')},
            'alt_text': {'label': _('النص البديل')},
            'order': {'label': _('ترتيب العرض')},
            'metadata': {'label': _('بيانات وصفية')},
        }

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_auction_title(self, obj):
        return obj.auction.title if obj.auction else None


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


class AuctionSerializer(BaseModelSerializer):
    """Serializer for Auction model"""
    images = AuctionImageSerializer(many=True, read_only=True, label=_('الصور'))
    property_details = serializers.SerializerMethodField(label=_('تفاصيل العقار'))
    cover_image_url = serializers.SerializerMethodField(label=_('رابط صورة الغلاف'))
    auction_type_display = serializers.CharField(source='get_auction_type_display', read_only=True, label=_('نوع المزاد المعروض'))
    status_display = serializers.CharField(source='get_status_display', read_only=True, label=_('الحالة المعروضة'))
    highest_bid = serializers.SerializerMethodField(label=_('أعلى مزايدة'))
    bids_count = serializers.SerializerMethodField(label=_('عدد المزايدات'))
    time_remaining = serializers.SerializerMethodField(label=_('الوقت المتبقي'))

    class Meta:
        model = Auction
        fields = [
            'id', 'uuid', 'title', 'auction_type', 'auction_type_display',
            'status', 'status_display', 'description', 'start_date', 'end_date',
            'registration_deadline', 'viewing_dates', 'timeline', 'related_property',
            'property_details', 'starting_bid', 'reserve_price', 'minimum_increment',
            'current_bid', 'estimated_value', 'bid_history', 'financial_terms',
            'buyer_premium_percent', 'registration_fee', 'deposit_required',
            'is_published', 'is_featured', 'is_private', 'cover_image',
            'cover_image_url', 'terms_conditions', 'special_notes', 'view_count',
            'bid_count', 'registered_bidders', 'analytics', 'highest_bid',
            'bids_count', 'time_remaining', 'images', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'uuid': {'read_only': True, 'label': _('معرف فريد')},
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
            'cover_image': {'label': _('صورة الغلاف')},
            'terms_conditions': {'label': _('الشروط والأحكام')},
            'special_notes': {'label': _('ملاحظات خاصة')},
            'analytics': {'label': _('بيانات تحليلية')},
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
                'cover_image_url': obj.related_property.cover_image.url if obj.related_property.cover_image else None,
                'size_sqm': obj.related_property.size_sqm,
                'bedrooms': obj.related_property.bedrooms,
                'bathrooms': obj.related_property.bathrooms,
            }
        return None

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
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
    file_url = serializers.SerializerMethodField(label=_('رابط الملف'))
    thumbnail_url = serializers.SerializerMethodField(label=_('رابط الصورة المصغرة'))
    uploaded_by_details = UserBriefSerializer(source='uploaded_by', read_only=True, label=_('تفاصيل الناشر'))
    verified_by_details = UserBriefSerializer(source='verified_by', read_only=True, label=_('تم التحقق بواسطة'))
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True, label=_('نوع الوثيقة المعروض'))
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True, label=_('حالة التحقق المعروضة'))

    class Meta:
        model = Document
        fields = [
            'id', 'document_number', 'title', 'document_type', 'document_type_display',
            'description', 'file', 'file_url', 'thumbnail', 'thumbnail_url',
            'verification_status', 'verification_status_display', 'verification_date',
            'verification_notes', 'verification_details', 'issue_date', 'expiry_date',
            'related_property', 'related_auction', 'related_contract', 'uploaded_by',
            'uploaded_by_details', 'verified_by', 'verified_by_details', 'file_size',
            'page_count', 'content_type', 'document_metadata', 'is_public',
            'access_code', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'document_number': {'read_only': True, 'label': _('رقم الوثيقة')},
            'uploaded_by': {'write_only': True, 'label': _('تم التحميل بواسطة')},
            'verified_by': {'write_only': True, 'label': _('تم التحقق بواسطة')},
            'file_size': {'read_only': True, 'label': _('حجم الملف (كيلوبايت)')},
            'page_count': {'read_only': True, 'label': _('عدد الصفحات')},
            'content_type': {'read_only': True, 'label': _('نوع المحتوى')},
            'verification_date': {'read_only': True, 'label': _('تاريخ التحقق')},
            'thumbnail': {'read_only': True, 'label': _('صورة مصغرة')},
            'title': {'label': _('العنوان')},
            'document_type': {'label': _('نوع الوثيقة')},
            'description': {'label': _('الوصف')},
            'file': {'label': _('ملف الوثيقة')},
            'verification_status': {'label': _('حالة التحقق')},
            'verification_notes': {'label': _('ملاحظات التحقق')},
            'verification_details': {'label': _('تفاصيل التحقق')},
            'issue_date': {'label': _('تاريخ الإصدار')},
            'expiry_date': {'label': _('تاريخ الانتهاء')},
            'related_property': {'label': _('العقار المرتبط')},
            'related_auction': {'label': _('المزاد المرتبط')},
            'related_contract': {'label': _('العقد المرتبط')},
            'document_metadata': {'label': _('بيانات الوثيقة')},
            'is_public': {'label': _('متاح للجميع')},
            'access_code': {'label': _('رمز الوصول')},
        }

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None


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
    file_url = serializers.SerializerMethodField(label=_('رابط الملف'))

    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'title', 'description', 'status', 'status_display',
            'contract_file', 'file_url', 'related_property', 'property_details',
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
            'contract_file': {'label': _('ملف العقد')},
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

    def get_file_url(self, obj):
        if obj.contract_file:
            return obj.contract_file.url
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
