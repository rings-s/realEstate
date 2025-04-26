import os
import uuid
from datetime import datetime
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import (
    MinValueValidator, MaxValueValidator,
    FileExtensionValidator, MinLengthValidator,
    RegexValidator
)

from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from accounts.models import CustomUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


# -------------------------------------------------------------------------
# Helper Functions for Image and File Uploads
# -------------------------------------------------------------------------




# Helper function to define upload paths
def file_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/resources/<resource_id>/<filename>
    return f'resources/{instance.id}/files/{filename}'

def image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/resources/<resource_id>/images/<filename>
    # Using resource.id assumes the Resource instance is saved first if image is added simultaneously.
    # Or, if ResourceImage is saved separately, instance.resource.id works.
    return f'resources/{instance.resource.id}/images/{filename}'

class RoleChoices:
    """Role constants"""
    ADMIN = 'admin'
    SELLER = 'seller'
    OWNER = 'owner'
    AGENT = 'agent'
    LEGAL = 'legal'
    INSPECTOR = 'inspector'
    BIDDER = 'bidder'

    CHOICES = [
        (ADMIN, _('Administrator')),
        (SELLER, _('Seller')),
        (OWNER, _('Property Owner')),
        (AGENT, _('Agent')),
        (LEGAL, _('Legal Advisor')),
        (INSPECTOR, _('Property Inspector')),
        (BIDDER, _('Bidder')),
    ]
# -------------------------------------------------------------------------
# Media Model
# -------------------------------------------------------------------------
class Media(models.Model):
    """
    A generic model to store uploaded files (images, documents, etc.)
    linked to any other model using GenericForeignKey.
    """
    # Choices for media type identification
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    ]

    file = models.FileField(upload_to='generic_media/%Y/%m/%d/', verbose_name="File")
    name = models.CharField(max_length=255, blank=True, verbose_name="Optional Name")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Uploaded At")
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPES,
        default='other',
        verbose_name="Media Type"
    )

    # Fields for GenericForeignKey
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.name or os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.basename(self.file.name)
        # Basic media type detection based on extension (can be expanded)
        if not self.pk or not self.media_type or self.media_type == 'other': # Detect only if new or not set
             _, extension = os.path.splitext(self.file.name)
             extension = extension.lower()
             if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                 self.media_type = 'image'
             elif extension in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']:
                 self.media_type = 'document'
             elif extension in ['.mp4', '.avi', '.mov', '.wmv', '.mkv']:
                 self.media_type = 'video'
             elif extension in ['.mp3', '.wav', '.ogg', '.aac']:
                 self.media_type = 'audio'
             else:
                 self.media_type = 'other'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "الملف"
        verbose_name_plural = "الملفات و الصور"
        ordering = ['-uploaded_at']


# -------------------------------------------------------------------------
# Messaging Models
# -------------------------------------------------------------------------
class MessageThread(models.Model):
    """Model for message threads/conversations"""
    THREAD_TYPES = [
        ('inquiry', _('استفسار')),
        ('auction', _('مزاد')),
        ('property', _('عقار')),
        ('contract', _('عقد')),
        ('support', _('دعم')),
        ('other', _('أخرى')),
    ]

    STATUS_CHOICES = [
        ('active', _('نشط')),
        ('archived', _('مؤرشف')),
        ('closed', _('مغلق')),
        ('deleted', _('محذوف')),
    ]

    uuid = models.UUIDField(_('معرف فريد'), default=uuid.uuid4, editable=False, unique=True)
    subject = models.CharField(_('الموضوع'), max_length=255)
    thread_type = models.CharField(_('نوع المحادثة'), max_length=20, choices=THREAD_TYPES)
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='active')

    # Related objects
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_threads',
        null=True,
        verbose_name=_('المنشئ')
    )
    related_property = models.ForeignKey(
        'Property',
        on_delete=models.SET_NULL,
        related_name='threads',
        null=True,
        blank=True,
        verbose_name=_('العقار المرتبط')
    )
    related_auction = models.ForeignKey(
        'Auction',
        on_delete=models.SET_NULL,
        related_name='threads',
        null=True,
        blank=True,
        verbose_name=_('المزاد المرتبط')
    )

    # Thread settings
    is_private = models.BooleanField(_('محادثة خاصة'), default=False)
    is_system_thread = models.BooleanField(_('محادثة نظام'), default=False)
    last_message_at = models.DateTimeField(_('وقت آخر رسالة'), null=True, blank=True)

    # Additional metadata for API
    metadata = models.JSONField(
        _('بيانات إضافية'),
        default=dict,
        blank=True,
        help_text=_('بيانات إضافية للواجهة الأمامية')
    )

    # Fields moved from BaseModel
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('محادثة')
        verbose_name_plural = _('المحادثات')
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['thread_type']),
            models.Index(fields=['status']),
            models.Index(fields=['-last_message_at']),
        ]

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        # Set last_message_at to created_at for new threads
        if not self.id and not self.last_message_at:
            self.last_message_at = timezone.now()
        super().save(*args, **kwargs)


class ThreadParticipant(models.Model):
    """Model for participants in a message thread"""
    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_('المحادثة')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='thread_participations',
        verbose_name=_('المستخدم')
    )
    role = models.CharField(
            _('دور المستخدم'),
            max_length=20,
            choices=RoleChoices.CHOICES,
            null=True,
            blank=True
        )

    # Status flags
    is_active = models.BooleanField(_('نشط'), default=True)
    is_muted = models.BooleanField(_('صامت'), default=False)
    last_read_at = models.DateTimeField(_('آخر قراءة'), null=True, blank=True)

    # Custom permissions as JSON
    custom_permissions = models.JSONField(_('صلاحيات مخصصة'), default=dict, blank=True)

    # Fields moved from BaseModel
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('مشارك في المحادثة')
        verbose_name_plural = _('المشاركون في المحادثة')
        unique_together = ['thread', 'user']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} in {self.thread.subject}"


class Message(models.Model):
    """Model for messages in threads"""
    MESSAGE_TYPES = [
        ('text', _('نص')),
        ('image', _('صورة')),
        ('file', _('ملف')),
        ('location', _('موقع')),
        ('system', _('رسالة نظام')),
    ]

    STATUS_CHOICES = [
        ('sending', _('جاري الإرسال')),
        ('sent', _('تم الإرسال')),
        ('delivered', _('تم التسليم')),
        ('read', _('تمت القراءة')),
        ('failed', _('فشل الإرسال')),
        ('deleted', _('محذوفة')),
    ]

    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('المحادثة')
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='sent_messages',
        null=True,
        verbose_name=_('المرسل')
    )
    content = models.TextField(_('المحتوى'))
    message_type = models.CharField(_('نوع الرسالة'), max_length=20, choices=MESSAGE_TYPES, default='text')
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='sent')

    # File or image attachment
    media = GenericRelation(
        Media,
        related_query_name='message',
        verbose_name=_('Media')
    )
    attachment_name = models.CharField(_('اسم المرفق'), max_length=255, blank=True)
    attachment_size = models.PositiveIntegerField(_('حجم المرفق'), null=True, blank=True)

    # Message metadata
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('رد على')
    )
    sent_at = models.DateTimeField(_('وقت الإرسال'), default=timezone.now)
    delivered_at = models.DateTimeField(_('وقت التسليم'), null=True, blank=True)
    read_at = models.DateTimeField(_('وقت القراءة'), null=True, blank=True)

    # Special flags
    is_system_message = models.BooleanField(_('رسالة نظام'), default=False)
    is_important = models.BooleanField(_('مهمة'), default=False)

    # Message metadata
    metadata = models.JSONField(_('بيانات وصفية'), default=dict, blank=True)

    # Fields moved from BaseModel
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('رسالة')
        verbose_name_plural = _('الرسائل')
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['thread', 'sent_at']),
            models.Index(fields=['sender', 'sent_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..." if len(self.content) > 50 else self.content

    def save(self, *args, **kwargs):
        # Set message type based on attachment
        if self.media and not self.message_type:
            self.message_type = self.media.media_type

            # Set attachment metadata
            self.attachment_name = os.path.basename(self.media.file.name)
            self.attachment_size = self.media.file.size if hasattr(self.media.file, 'size') else None

        # For new messages, update thread's last_message_at
        is_new = self.pk is None

        # Save the message
        super().save(*args, **kwargs)

        # Update thread last_message_at
        if is_new and self.thread:
            self.thread.last_message_at = self.sent_at
            self.thread.save(update_fields=['last_message_at'])


# -------------------------------------------------------------------------
# Property Models
# -------------------------------------------------------------------------
class Property(models.Model):
    """Model for real estate properties"""
    PROPERTY_TYPES = [
        ('residential', _('سكني')),
        ('commercial', _('تجاري')),
        ('land', _('أرض')),
        ('industrial', _('صناعي')),
        ('mixed_use', _('متعدد الاستخدام')),
    ]

    BUILDING_TYPE_CHOICES = [
        ('apartment', _('شقة')),
        ('villa', _('فيلا')),
        ('building', _('عمارة')),
        ('farmhouse', _('مزرعة')),
        ('chalet', _('شاليه')),
        ('warehouse', _('مستودع')),
        ('shop', _('محل تجاري')),
        ('office', _('مكتب')),
        ('hotel', _('فندق')),
    ]

    STATUS_CHOICES = [
        ('available', _('متاح')),
        ('under_contract', _('تحت العقد')),
        ('sold', _('مباع')),
        ('off_market', _('خارج السوق')),
        ('auction', _('في المزاد')),
    ]

    # Basic information
    property_number = models.CharField(_('رقم العقار'), max_length=50, unique=True)
    title = models.CharField(_('العنوان'), max_length=255)
    property_type = models.CharField(_('نوع العقار'), max_length=20, choices=PROPERTY_TYPES)
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='available')
    view_count = models.PositiveIntegerField(_('عدد المشاهدات'), default=0)

    deed_number = models.CharField(
        _('رقم الصك'),
        max_length=100,
        unique=True,  # Make it unique
        help_text=_('رقم صك الملكية الرسمي للعقار')
    )

    # Location as JSON - better for API
    location = models.JSONField(
        _('الموقع الجغرافي'),
        default=dict,
        blank=True,
        help_text=_('يحتوي على خط العرض وخط الطول واسم المدينة والعنوان')
        # Example: {"latitude": 24.774265, "longitude": 46.738586, "city": "الرياض", "address": "شارع العليا"}
    )

    # Keep individual location fields for backward compatibility
    address = models.CharField(_('العنوان'), max_length=255)
    city = models.CharField(_('المدينة'), max_length=100)
    state = models.CharField(_('المنطقة/المحافظة'), max_length=100)
    postal_code = models.CharField(_('الرمز البريدي'), max_length=20, blank=True)
    country = models.CharField(_('الدولة'), max_length=100, default='المملكة العربية السعودية')
    highQualityStreets = models.JSONField(_('الشوارع الراقية'), default=list, blank=True)  # Fixed duplicate default

    # Property details
    description = models.TextField(_('الوصف'))

    # JSON fields for better API structure
    features = models.JSONField(
        _('المميزات'),
        default=list,
        blank=True,
        help_text=_('قائمة بالمميزات الرئيسية للعقار')
        # Example: ["حديقة", "مسبح", "موقف سيارات"]
    )

    amenities = models.JSONField(
        _('المرافق'),
        default=list,
        blank=True,
        help_text=_('قائمة بالمرافق المتاحة')
        # Example: ["نادي رياضي", "حراسة أمنية", "خدمة تنظيف"]
    )

    rooms = models.JSONField(
        _('الغرف'),
        default=list,
        blank=True,
        help_text=_('تفاصيل الغرف وأحجامها')
        # Example: [{"type": "غرفة نوم", "size": 25, "features": ["شرفة", "حمام خاص"]}, ...]
    )

    specifications = models.JSONField(
        _('المواصفات'),
        default=dict,
        blank=True,
        help_text=_('مواصفات العقار التفصيلية')
        # Example: {"floor_type": "رخام", "windows": "زجاج مزدوج", "ceiling_height": 3.5}
    )

    # Basic numerical specs
    size_sqm = models.DecimalField(_('المساحة (متر مربع)'), max_digits=10, decimal_places=2, null=True, blank=True)
    bedrooms = models.PositiveSmallIntegerField(_('عدد غرف النوم'), null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField(_('عدد الحمامات'), null=True, blank=True)
    floors = models.PositiveSmallIntegerField(_('عدد الطوابق'), null=True, blank=True)
    parking_spaces = models.PositiveSmallIntegerField(_('أماكن وقوف السيارات'), null=True, blank=True)
    year_built = models.PositiveIntegerField(
        _('سنة البناء'),
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(datetime.now().year)
        ]
    )

    # Financial information
    market_value = models.DecimalField(_('القيمة السوقية'), max_digits=14, decimal_places=2, null=True, blank=True)
    minimum_bid = models.DecimalField(_('الحد الأدنى للمزايدة'), max_digits=14, decimal_places=2, null=True, blank=True)

    # JSON field for pricing history and details
    pricing_details = models.JSONField(
        _('تفاصيل التسعير'),
        default=dict,
        blank=True,
        help_text=_('تاريخ التسعير وتفاصيل أخرى')
        # Example: {"history": [{"date": "2023-01-01", "price": 1000000}, ...], "valuation_method": "تقييم مستقل"}
    )

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='owned_properties',
        null=True,
        blank=True,
        verbose_name=_('المالك')
    )

    # Publication status
    is_published = models.BooleanField(_('منشور'), default=False)
    is_featured = models.BooleanField(_('مميز'), default=False)
    is_verified = models.BooleanField(_('موثق'), default=False)

    # SEO and sharing
    slug = models.SlugField(_('الرابط المختصر'), max_length=255, unique=True, blank=True)

    # Cover image - main property image
    media = GenericRelation(
        Media,
        related_query_name='property',
        verbose_name=_('Media')
    )

    # Additional metadata for API
    metadata = models.JSONField(
        _('بيانات إضافية'),
        default=dict,
        blank=True,
        help_text=_('بيانات إضافية للواجهة الأمامية')
    )

    # Fields moved from BaseModel
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('عقار')
        verbose_name_plural = _('العقارات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property_number']),
            models.Index(fields=['deed_number']),
            models.Index(fields=['status']),
            models.Index(fields=['property_type']),
            models.Index(fields=['city']),
            models.Index(fields=['state']),
            models.Index(fields=['is_published']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['market_value']),
            models.Index(fields=['owner']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            # Compound indexes (if you often filter by combinations)
            models.Index(fields=['is_published', 'is_featured']),
            models.Index(fields=['city', 'property_type']),
            models.Index(fields=['status', 'market_value']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate property number if not provided
        if not self.property_number:
            prefix = self.property_type[:3].upper()
            import random
            random_num = random.randint(10000, 99999)
            self.property_number = f"{prefix}-{random_num}"

        # Generate slug if not provided
        if not self.slug:
            from .utils import arabic_slugify
            self.slug = arabic_slugify(self.title)

            # Ensure uniqueness - use safer approach to avoid connection attribute error
            try:
                original_slug = self.slug
                count = 1
                max_attempts = 100
                attempts = 0

                # Fix: Don't use connection.schema_editor.connection which causes the error
                # Instead, directly check for existing slugs
                from django.db import connection
                table_exists = False

                try:
                    # Check if the table exists by running a simple query
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT 1 FROM information_schema.tables WHERE table_name = %s",
                            [self._meta.db_table]
                        )
                        table_exists = cursor.fetchone() is not None
                except Exception:
                    # If we can't check (e.g., during migrations), assume table doesn't exist
                    table_exists = False

                # Only check for existing slugs if the table exists
                if table_exists:
                    while attempts < max_attempts:
                        # Check if slug exists (excluding this instance)
                        query = Property.objects.filter(slug=self.slug)
                        if self.pk:
                            query = query.exclude(pk=self.pk)

                        if not query.exists():
                            break

                        # Create a new slug with a counter
                        self.slug = f"{original_slug}-{count}"
                        count += 1
                        attempts += 1
            except Exception as e:
                # If any error occurs during slug checking, log it and continue
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error checking slug uniqueness: {str(e)}")

        # Ensure location JSON is properly formatted and populated from individual fields
        if not self.location:
            self.location = {
                "latitude": None,
                "longitude": None,
                "city": self.city,
                "address": self.address,
                "postal_code": self.postal_code,
                "state": self.state,
                "country": self.country
            }

        # Save the model
        super().save(*args, **kwargs)



# -------------------------------------------------------------------------
# Auction Models
# -------------------------------------------------------------------------
class Auction(models.Model):
    """Model for property auctions"""
    AUCTION_TYPES = [
        ('sealed', _('مزاد العطاءات المغلقة')),
        ('reserve', _('مزاد بحد أدنى')),
        ('no_reserve', _('مزاد بدون حد أدنى')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('scheduled', _('مجدول')),
        ('live', _('مباشر')),
        ('ended', _('منتهي')),
        ('cancelled', _('ملغي')),
        ('completed', _('مكتمل')),
    ]

    # Basic information
    title = models.CharField(_('العنوان'), max_length=255)
    slug = models.SlugField(_('الرابط المختصر'), max_length=255, unique=True, blank=True)
    auction_type = models.CharField(_('نوع المزاد'), max_length=20, choices=AUCTION_TYPES)
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='draft')
    description = models.TextField(_('الوصف'))

    # Dates and timing
    start_date = models.DateTimeField(_('تاريخ البدء'))
    end_date = models.DateTimeField(_('تاريخ الانتهاء'))
    registration_deadline = models.DateTimeField(_('موعد انتهاء التسجيل'), null=True, blank=True)

    # Viewing dates as JSON for better API structure
    viewing_dates = models.JSONField(
        _('مواعيد المعاينة'),
        default=list,
        blank=True,
        help_text=_('تواريخ وأوقات المعاينة المتاحة')
    )

    # Auction schedule and timeline
    timeline = models.JSONField(
        _('الجدول الزمني'),
        default=list,
        blank=True,
        help_text=_('مراحل المزاد المختلفة وتواريخها')
    )

    # Related property
    related_property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='auctions',
        verbose_name=_('العقار المرتبط')
    )

    # Financial details
    starting_bid = models.DecimalField(_('المزايدة الأولية'), max_digits=14, decimal_places=2)
    reserve_price = models.DecimalField(_('السعر المحفوظ'), max_digits=14, decimal_places=2, null=True, blank=True)
    minimum_increment = models.DecimalField(_('الحد الأدنى للزيادة'), max_digits=14, decimal_places=2, default=100.00)
    current_bid = models.DecimalField(_('المزايدة الحالية'), max_digits=14, decimal_places=2, null=True, blank=True)
    estimated_value = models.DecimalField(_('القيمة التقديرية'), max_digits=14, decimal_places=2, null=True, blank=True)

    # Bid history as JSON for better API access
    bid_history = models.JSONField(
        _('سجل المزايدات'),
        default=list,
        blank=True,
        editable=False,
        help_text=_('سجل المزايدات وتفاصيلها')
    )

    # Financial terms as JSON for better API structure
    financial_terms = models.JSONField(
        _('الشروط المالية'),
        default=dict,
        blank=True,
        help_text=_('تفاصيل وشروط الدفع والرسوم')
    )

    # Fees and deposits
    buyer_premium_percent = models.DecimalField(_('عمولة المشتري (%)'), max_digits=5, decimal_places=2, default=0)
    registration_fee = models.DecimalField(_('رسوم التسجيل'), max_digits=10, decimal_places=2, default=0)
    deposit_required = models.DecimalField(_('التأمين المطلوب'), max_digits=14, decimal_places=2, default=0)

    # Publication status
    is_published = models.BooleanField(_('منشور'), default=False)
    is_featured = models.BooleanField(_('مميز'), default=False)
    is_private = models.BooleanField(_('مزاد خاص'), default=False)

    # Cover image for the auction
    media = GenericRelation(
        Media,
        related_query_name='auction',
        verbose_name=_('Media')
    )

    # Auction rules and terms
    terms_conditions = models.TextField(_('الشروط والأحكام'), blank=True)
    special_notes = models.TextField(_('ملاحظات خاصة'), blank=True)

    # For tracking purposes
    view_count = models.PositiveIntegerField(_('عدد المشاهدات'), default=0)
    bid_count = models.PositiveIntegerField(_('عدد المزايدات'), default=0)
    registered_bidders = models.PositiveIntegerField(_('المزايدين المسجلين'), default=0)

    # Analytics data for API
    analytics = models.JSONField(
        _('بيانات تحليلية'),
        default=dict,
        blank=True,
        help_text=_('إحصائيات وبيانات تحليلية عن المزاد')
    )

    # Fields moved from BaseModel
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('مزاد')
        verbose_name_plural = _('المزادات')
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['is_published', 'is_featured']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            from .utils import arabic_slugify
            self.slug = arabic_slugify(self.title)

            # Ensure uniqueness
            from django.db import models
            original_slug = self.slug
            count = 1
            while Auction.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{original_slug}-{count}"
                count += 1

        # If using related_property's cover image when none is set
        if not hasattr(self, 'pk') or not self.pk:
            super().save(*args, **kwargs)
            if not self.media.exists() and self.related_property and self.related_property.media.exists():
                # Copy the property's media to this auction
                for media_item in self.related_property.media.all():
                    self.media.create(
                        file=media_item.file,
                        name=media_item.name,
                        media_type=media_item.media_type
                    )
        else:
            super().save(*args, **kwargs)



class Bid(models.Model):
    """Model for auction bids"""
    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('accepted', _('مقبول')),
        ('rejected', _('مرفوض')),
        ('cancelled', _('ملغي')),
        ('outbid', _('تمت المزايدة بأعلى')),
        ('winning', _('فائز')),
    ]

    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name=_('المزاد')
    )
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name=_('المزايد')
    )
    bid_amount = models.DecimalField(_('مبلغ المزايدة'), max_digits=14, decimal_places=2)
    bid_time = models.DateTimeField(_('وقت المزايدة'), default=timezone.now)
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='pending')

    # For auto bidding feature
    is_auto_bid = models.BooleanField(_('مزايدة تلقائية'), default=False)
    max_auto_bid = models.DecimalField(_('الحد الأقصى للمزايدة التلقائية'), max_digits=14, decimal_places=2, null=True, blank=True)

    # Additional information
    ip_address = models.GenericIPAddressField(_('عنوان IP'), blank=True, null=True)
    user_agent = models.TextField(_('وكيل المستخدم'), blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    # Additional metadata for API
    metadata = models.JSONField(
        _('بيانات إضافية'),
        default=dict,
        blank=True,
        help_text=_('بيانات إضافية عن المزايدة')
        # Example: {"device_type": "mobile", "location": {"city": "الرياض", "country": "السعودية"}}
    )

    # Payment information JSON
    payment_info = models.JSONField(
        _('معلومات الدفع'),
        default=dict,
        blank=True,
        help_text=_('معلومات عن حالة الدفع والتأمين للمزايدة')
        # Example: {"deposit_paid": true, "deposit_amount": 5000, "payment_method": "bank_transfer", "payment_date": "2023-01-15"}
    )

    # Fields moved from BaseModel
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('مزايدة')
        verbose_name_plural = _('المزايدات')
        ordering = ['-bid_time']
        indexes = [
            models.Index(fields=['auction', '-bid_time']),
            models.Index(fields=['bidder', '-bid_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.bidder} زايد بمبلغ {self.bid_amount} على {self.auction.title}"

    def save(self, *args, **kwargs):
        # For new bids, update auction stats
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Update auction bid count
            self.auction.bid_count += 1

            # Update current bid if this is the highest
            if not self.auction.current_bid or self.bid_amount > self.auction.current_bid:
                self.auction.current_bid = self.bid_amount

                # Mark all other bids as outbid
                if self.status == 'accepted':
                    Bid.objects.filter(
                        auction=self.auction,
                        status='winning'
                    ).exclude(id=self.id).update(status='outbid')

                    # Mark this as winning
                    self.status = 'winning'
                    self.save(update_fields=['status'])

            # Update bid history in auction's JSON field
            try:
                bid_entry = {
                    "id": self.id,
                    "bidder_id": self.bidder.id,
                    "bidder_name": self.bidder.get_full_name() or self.bidder.email,
                    "amount": float(self.bid_amount),
                    "time": self.bid_time.isoformat(),
                    "status": self.status,
                }

                # Get current history, add new bid, save back
                history = self.auction.bid_history
                history.append(bid_entry)
                self.auction.bid_history = history
            except Exception:
                # Don't prevent saving if history update fails
                pass

            # Save the auction
            self.auction.save(update_fields=['bid_count', 'current_bid', 'bid_history'])


# -------------------------------------------------------------------------
# Document Models
# -------------------------------------------------------------------------
class Document(models.Model):
    """Model for document files"""
    DOCUMENT_TYPES = [
        ('deed', _('صك ملكية')),
        ('contract', _('عقد')),
        ('certificate', _('شهادة')),
        ('report', _('تقرير فحص')),
        ('identity', _('وثيقة هوية')),
        ('financial', _('وثيقة مالية')),
        ('other', _('أخرى')),
    ]

    VERIFICATION_STATUS = [
        ('pending', _('قيد الانتظار')),
        ('verified', _('تم التحقق')),
        ('rejected', _('مرفوض')),
    ]

    document_number = models.CharField(_('رقم الوثيقة'), max_length=50, unique=True)
    title = models.CharField(_('العنوان'), max_length=255)
    document_type = models.CharField(_('نوع الوثيقة'), max_length=20, choices=DOCUMENT_TYPES)
    description = models.TextField(_('الوصف'), blank=True)

    # File field with validation
    media = GenericRelation(
        Media,
        related_query_name='document',
        verbose_name=_('Media')
    )

    # Thumbnail for quick preview
    thumbnail = models.ImageField(
        _('صورة مصغرة'),
        upload_to='documents/thumbnails/',
        blank=True,
        null=True,
        editable=False
    )

    # Verification
    verification_status = models.CharField(
        _('حالة التحقق'),
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    verification_date = models.DateTimeField(_('تاريخ التحقق'), null=True, blank=True)
    verification_notes = models.TextField(_('ملاحظات التحقق'), blank=True)

    # Verification details as JSON for API
    verification_details = models.JSONField(
        _('تفاصيل التحقق'),
        default=dict,
        blank=True,
        help_text=_('تفاصيل إضافية عن عملية التحقق')
        # Example: {"method": "تحقق يدوي", "verified_fields": ["توقيع", "ختم"], "verification_id": "VER-12345"}
    )

    # Document dates
    issue_date = models.DateField(_('تاريخ الإصدار'), null=True, blank=True)
    expiry_date = models.DateField(_('تاريخ الانتهاء'), null=True, blank=True)

    # Relations
    related_property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        verbose_name=_('العقار المرتبط')
    )
    related_auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        verbose_name=_('المزاد المرتبط')
    )
    related_contract = models.ForeignKey(
        'Contract',
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        verbose_name=_('العقد المرتبط')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='uploaded_documents',
        null=True,
        verbose_name=_('تم التحميل بواسطة')
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='verified_documents',
        null=True,
        blank=True,
        verbose_name=_('تم التحقق بواسطة')
    )

    # File metadata
    file_size = models.PositiveIntegerField(_('حجم الملف (كيلوبايت)'), blank=True, null=True, editable=False)
    page_count = models.PositiveIntegerField(_('عدد الصفحات'), blank=True, null=True, editable=False)
    content_type = models.CharField(_('نوع المحتوى'), max_length=100, blank=True, editable=False)

    # Document metadata as JSON for API
    document_metadata = models.JSONField(
        _('بيانات الوثيقة'),
        default=dict,
        blank=True,
        help_text=_('بيانات تفصيلية عن الوثيقة')
        # Example: {"issuer": "وزارة العدل", "document_id": "123456", "reference_number": "REF-789"}
    )

    # Security and access
    is_public = models.BooleanField(_('متاح للجميع'), default=False)
    access_code = models.CharField(_('رمز الوصول'), max_length=50, blank=True)

    # Fields moved from BaseModel
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('وثيقة')
        verbose_name_plural = _('الوثائق')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['document_type']),
            models.Index(fields=['verification_status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate document number if not provided
        if not self.document_number:
            prefix = self.document_type[:3].upper()
            import random
            random_num = random.randint(10000, 99999)
            self.document_number = f"{prefix}-{random_num}"

        # Save file metadata if file exists
        if self.media and hasattr(self.media.file, 'file'):
            # Get file size in KB
            if hasattr(self.media.file, 'size'):
                self.file_size = self.media.file.size // 1024

            # Set content type
            file_name = self.media.file.name.lower()
            if file_name.endswith('.pdf'):
                self.content_type = 'application/pdf'
            elif file_name.endswith('.doc'):
                self.content_type = 'application/msword'
            elif file_name.endswith('.docx'):
                self.content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_name.endswith(('.jpg', '.jpeg')):
                self.content_type = 'image/jpeg'
            elif file_name.endswith('.png'):
                self.content_type = 'image/png'

            # Generate thumbnail for PDFs and images
            try:
                if file_name.endswith('.pdf'):
                    # This would require PyMuPDF (fitz) in production
                    # Logic omitted for brevity
                    pass
                elif file_name.endswith(('.jpg', '.jpeg', '.png')):
                    from PIL import Image
                    from io import BytesIO
                    from django.core.files.base import ContentFile

                    # Open the image
                    img = Image.open(self.media.file)

                    # Create thumbnail
                    img.thumbnail((200, 200))

                    # Save thumbnail
                    thumb_io = BytesIO()
                    img_format = 'JPEG'
                    img.save(thumb_io, format=img_format, quality=70)

                    # Save to thumbnail field
                    thumb_name = f"{os.path.splitext(os.path.basename(self.media.file.name))[0]}_thumb.jpg"
                    self.thumbnail.save(thumb_name, ContentFile(thumb_io.getvalue()), save=False)
            except Exception:
                # Don't prevent saving if thumbnail generation fails
                pass

        # Handle verification status change
        if self.verification_status == 'verified' and not self.verification_date:
            self.verification_date = timezone.now()

        super().save(*args, **kwargs)


# -------------------------------------------------------------------------
# Contract Model
# -------------------------------------------------------------------------
class Contract(models.Model):
    """Model for property contracts"""
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('pending', _('بانتظار الموافقة')),
        ('active', _('نشط')),
        ('fulfilled', _('تم الوفاء')),
        ('cancelled', _('ملغي')),
        ('expired', _('منتهي')),
        ('disputed', _('متنازع عليه')),
    ]

    PAYMENT_METHODS = [
        ('full_payment', _('دفعة كاملة')),
        ('installments', _('أقساط')),
        ('mortgage', _('رهن عقاري')),
        ('custom', _('خطة دفع مخصصة')),
    ]

    # Basic information
    contract_number = models.CharField(_('رقم العقد'), max_length=50, unique=True)
    title = models.CharField(_('العنوان'), max_length=255)
    description = models.TextField(_('الوصف'), blank=True)
    status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='draft')

    # Contract file
    media = GenericRelation(
        Media,
        related_query_name='contract',
        verbose_name=_('Media')
    )

    # Related entities
    related_property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name=_('العقار المرتبط')
    )
    related_auction = models.ForeignKey(
        Auction,
        on_delete=models.SET_NULL,
        related_name='contracts',
        null=True,
        blank=True,
        verbose_name=_('المزاد المرتبط')
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='buyer_contracts',
        verbose_name=_('المشتري')
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='seller_contracts',
        verbose_name=_('البائع')
    )

    # Contract details
    contract_date = models.DateField(_('تاريخ العقد'))
    effective_date = models.DateField(_('تاريخ السريان'), null=True, blank=True)
    expiry_date = models.DateField(_('تاريخ الانتهاء'), null=True, blank=True)

    # Contract timeline as JSON for API
    timeline = models.JSONField(
        _('الجدول الزمني'),
        default=list,
        blank=True,
        help_text=_('المراحل الزمنية للعقد')
        # Example: [{"phase": "توقيع العقد", "date": "2023-01-15", "completed": true}, {"phase": "تسليم العقار", "date": "2023-02-01", "completed": false}]
    )

    # Financial details
    total_amount = models.DecimalField(_('المبلغ الإجمالي'), max_digits=14, decimal_places=2)
    down_payment = models.DecimalField(_('الدفعة الأولى'), max_digits=14, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(_('طريقة الدفع'), max_length=20, choices=PAYMENT_METHODS)
    payment_terms = models.TextField(_('شروط الدفع'), blank=True)

    # Payment details as JSON for API
    payment_details = models.JSONField(
        _('تفاصيل الدفع'),
        default=dict,
        blank=True,
        help_text=_('تفاصيل وجدول الدفعات')
        # Example: {"installments": [{"amount": 10000, "due_date": "2023-03-01"}, {"amount": 10000, "due_date": "2023-04-01"}], "total_paid": 5000, "remaining": 15000}
    )

    # Payment tracking
    payments_history = models.JSONField(
        _('سجل المدفوعات'),
        default=list,
        blank=True,
        help_text=_('سجل تاريخي للمدفوعات المتعلقة بالعقد')
        # Example: [{"date": "2023-02-01", "amount": 5000, "type": "down_payment", "status": "completed", "reference": "PAY123"}]
    )

    # Additional details
    special_conditions = models.TextField(_('شروط خاصة'), blank=True)

    # Verification
    is_verified = models.BooleanField(_('تم التحقق'), default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='verified_contracts',
        null=True,
        blank=True,
        verbose_name=_('تم التحقق بواسطة')
    )
    verification_date = models.DateTimeField(_('تاريخ التحقق'), null=True, blank=True)

    # Signatures and completion
    buyer_signed = models.BooleanField(_('توقيع المشتري'), default=False)
    buyer_signed_date = models.DateTimeField(_('تاريخ توقيع المشتري'), null=True, blank=True)
    seller_signed = models.BooleanField(_('توقيع البائع'), default=False)
    seller_signed_date = models.DateTimeField(_('تاريخ توقيع البائع'), null=True, blank=True)

    # Parties and signatures as JSON for API
    parties = models.JSONField(
        _('الأطراف'),
        default=list,
        blank=True,
        help_text=_('تفاصيل أطراف العقد')
        # Example: [{"role": "buyer", "user_id": 123, "name": "أحمد محمد", "signature_status": "signed", "signature_date": "2023-01-15T10:30:00Z"}, ...]
    )

    # Fields moved from BaseModel
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('عقد')
        verbose_name_plural = _('العقود')
        ordering = ['-contract_date']
        indexes = [
            models.Index(fields=['contract_number']),
            models.Index(fields=['status']),
            models.Index(fields=['contract_date']),
            models.Index(fields=['buyer']),
            models.Index(fields=['seller']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate contract number if not provided
        if not self.contract_number:
            import random
            year = timezone.now().strftime('%Y')
            random_num = random.randint(1000, 9999)
            self.contract_number = f"CTR-{year}-{random_num}"

        # Handle status changes based on signatures
        if self.buyer_signed and self.seller_signed and self.status == 'pending':
            self.status = 'active'

        super().save(*args, **kwargs)

        # Update property status if contract is active
        if self.status == 'active' and self.related_property:
            self.related_property.status = 'under_contract'
            self.related_property.save(update_fields=['status'])
        elif self.status == 'fulfilled' and self.related_property:
            self.related_property.status = 'sold'
            self.related_property.save(update_fields=['status'])


# -------------------------------------------------------------------------
# Notification Models
# -------------------------------------------------------------------------
class Notification(models.Model):
    """Model for user notifications"""
    NOTIFICATION_TYPES = [
        ('auction_start', _('بدء المزاد')),
        ('auction_end', _('انتهاء المزاد')),
        ('outbid', _('تمت المزايدة بسعر أعلى')),
        ('bid_success', _('مزايدة ناجحة')),
        ('bid_failed', _('مزايدة فاشلة')),
        ('auction_won', _('تم الفوز بالمزاد')),
        ('payment_due', _('استحقاق الدفع')),
        ('payment_received', _('استلام الدفع')),
        ('message', _('رسالة جديدة')),
        ('document', _('تحديث الوثيقة')),
        ('system', _('إشعار نظام')),
        ('other', _('أخرى')),
    ]

    CHANNEL_CHOICES = [
        ('app', _('داخل التطبيق')),
        ('email', _('بريد إلكتروني')),
        ('sms', _('رسالة نصية')),
        ('push', _('إشعار فوري')),
        ('all', _('جميع القنوات')),
    ]

    # Basic information
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('المستلم')
    )
    notification_type = models.CharField(_('نوع الإشعار'), max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(_('العنوان'), max_length=255)
    content = models.TextField(_('المحتوى'))

    # Delivery status
    channel = models.CharField(_('القناة'), max_length=20, choices=CHANNEL_CHOICES, default='app')
    is_read = models.BooleanField(_('مقروءة'), default=False)
    read_at = models.DateTimeField(_('وقت القراءة'), null=True, blank=True)
    is_sent = models.BooleanField(_('تم الإرسال'), default=False)
    sent_at = models.DateTimeField(_('وقت الإرسال'), null=True, blank=True)

    # Related entities
    related_thread = models.ForeignKey(
        MessageThread,
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name=_('المحادثة المرتبطة')
    )
    related_auction = models.ForeignKey(
        Auction,
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name=_('المزاد المرتبط')
    )
    related_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name=_('العقار المرتبط')
    )
    related_contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name=_('العقد المرتبط')
    )

    # Deep link
    action_url = models.CharField(_('رابط الإجراء'), max_length=255, blank=True)

    # Priority
    is_important = models.BooleanField(_('مهم'), default=False)
    expiry_date = models.DateTimeField(_('تاريخ انتهاء الصلاحية'), null=True, blank=True)

    # Extended notification data for API
    notification_data = models.JSONField(
        _('بيانات الإشعار'),
        default=dict,
        blank=True,
        help_text=_('بيانات إضافية عن الإشعار')
        # Example: {"auction_details": {"title": "مزاد فيلا الرياض", "current_bid": 1500000}, "action_type": "view_auction"}
    )

    # Fields moved from BaseModel
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        verbose_name = _('إشعار')
        verbose_name_plural = _('الإشعارات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_read']),
            models.Index(fields=['is_sent']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"

    def mark_as_read(self):
        """Mark the notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_sent(self):
        """Mark the notification as sent"""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save(update_fields=['is_sent', 'sent_at'])
