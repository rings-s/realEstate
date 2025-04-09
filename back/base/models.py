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
from accounts.models import CustomUser, Role


# -------------------------------------------------------------------------
# Helper Functions for Image and File Uploads
# -------------------------------------------------------------------------

def validate_image_size(file):
    """Validate that image size is under 5MB"""
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        raise ValidationError(_('حجم الصورة يجب أن يكون أقل من 5 ميجابايت'))


def property_image_path(instance, filename):
    """Generate a unique path for property images"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('properties', str(instance.property.id), 'images', filename)


def auction_image_path(instance, filename):
    """Generate a unique path for auction images"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('auctions', str(instance.auction.id), 'images', filename)


def document_file_path(instance, filename):
    """Generate a unique path for document files"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    slug = slugify(instance.title)
    filename = f"{slug}-{uuid.uuid4()}.{ext}"

    # Organize by document type and year
    doc_type = slugify(instance.document_type)
    year = instance.created_at.strftime('%Y') if instance.created_at else datetime.now().strftime('%Y')
    return os.path.join('documents', doc_type, year, filename)


def contract_file_path(instance, filename):
    """Generate a unique path for contract files"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    filename = f"contract-{instance.contract_number}-{uuid.uuid4()}.{ext}"
    return os.path.join('contracts', filename)


# -------------------------------------------------------------------------
# Base Models
# -------------------------------------------------------------------------

class BaseModel(models.Model):
    """Base model with common fields for all models"""
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)

    class Meta:
        abstract = True


class BaseImageModel(BaseModel):
    """Base model for all image models"""
    alt_text = models.CharField(_('النص البديل'), max_length=255, blank=True)
    width = models.PositiveIntegerField(_('العرض'), blank=True, null=True, editable=False)
    height = models.PositiveIntegerField(_('الارتفاع'), blank=True, null=True, editable=False)
    file_size = models.PositiveIntegerField(_('حجم الملف (كيلوبايت)'), blank=True, null=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Save image metadata if the image file exists
        if hasattr(self, 'image') and self.image and hasattr(self.image, 'file'):
            try:
                from PIL import Image
                img = Image.open(self.image)
                self.width, self.height = img.size

                # Calculate file size in KB
                if hasattr(self.image, 'size'):
                    self.file_size = self.image.size // 1024
            except Exception:
                # Don't prevent saving if image processing fails
                pass

        super().save(*args, **kwargs)


# -------------------------------------------------------------------------
# Messaging Models
# -------------------------------------------------------------------------

class MessageThread(BaseModel):
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


class ThreadParticipant(BaseModel):
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
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        related_name='thread_participants',
        null=True,
        blank=True,
        verbose_name=_('دور المستخدم')
    )

    # Status flags
    is_active = models.BooleanField(_('نشط'), default=True)
    is_muted = models.BooleanField(_('صامت'), default=False)
    last_read_at = models.DateTimeField(_('آخر قراءة'), null=True, blank=True)

    # Custom permissions as JSON
    custom_permissions = models.JSONField(_('صلاحيات مخصصة'), default=dict, blank=True)

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


class Message(BaseModel):
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
    attachment = models.FileField(
        _('المرفق'),
        upload_to='messages/attachments/%Y/%m/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip']
            ),
        ]
    )
    attachment_type = models.CharField(_('نوع المرفق'), max_length=100, blank=True)
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
        if self.attachment and not self.message_type:
            ext = self.attachment.name.split('.')[-1].lower() if '.' in self.attachment.name else ''
            if ext in ['jpg', 'jpeg', 'png', 'gif']:
                self.message_type = 'image'
            else:
                self.message_type = 'file'

            # Set attachment metadata
            self.attachment_name = os.path.basename(self.attachment.name)
            self.attachment_type = self.attachment.content_type if hasattr(self.attachment, 'content_type') else ''
            self.attachment_size = self.attachment.size if hasattr(self.attachment, 'size') else None

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

class Property(BaseModel):
    """Model for real estate properties"""
    PROPERTY_TYPES = [
        ('residential', _('سكني')),
        ('commercial', _('تجاري')),
        ('land', _('أرض')),
        ('industrial', _('صناعي')),
        ('mixed_use', _('متعدد الاستخدام')),
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
    meta_title = models.CharField(_('عنوان الميتا'), max_length=100, blank=True)
    meta_description = models.TextField(_('وصف الميتا'), blank=True)

    # Cover image - main property image
    cover_image = models.ImageField(
        _('صورة الغلاف'),
        upload_to='properties/covers/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ]
    )

    # Additional metadata for API
    metadata = models.JSONField(
        _('بيانات إضافية'),
        default=dict,
        blank=True,
        help_text=_('بيانات إضافية للواجهة الأمامية')
    )

    class Meta:
        verbose_name = _('عقار')
        verbose_name_plural = _('العقارات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property_number']),
            models.Index(fields=['status']),
            models.Index(fields=['property_type']),
            models.Index(fields=['city']),
            models.Index(fields=['is_published', 'is_featured']),
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
            self.slug = slugify(self.title)
            # Ensure uniqueness
            original_slug = self.slug
            count = 1
            while Property.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{count}"
                count += 1

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


class PropertyImage(BaseImageModel):
    """Model for property images"""
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('العقار')
    )
    image = models.ImageField(
        _('الصورة'),
        upload_to=property_image_path,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ]
    )
    is_primary = models.BooleanField(_('صورة رئيسية'), default=False)
    caption = models.CharField(_('التعليق'), max_length=255, blank=True)
    order = models.PositiveIntegerField(_('ترتيب العرض'), default=0)

    # Additional metadata for the image
    metadata = models.JSONField(
        _('بيانات وصفية'),
        default=dict,
        blank=True,
        help_text=_('معلومات إضافية عن الصورة مثل الموقع أو الغرفة')
        # Example: {"room": "غرفة المعيشة", "taken_at": "2023-01-15"}
    )

    class Meta:
        verbose_name = _('صورة العقار')
        verbose_name_plural = _('صور العقار')
        ordering = ['order', '-is_primary', 'id']

    def __str__(self):
        return f"صورة للعقار {self.property.title} ({self.id})"

    def save(self, *args, **kwargs):
        # If this is marked as primary, unmark other primary images
        if self.is_primary:
            PropertyImage.objects.filter(
                property=self.property,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)

            # Also update the property's cover image
            if self.property and self.image:
                self.property.cover_image = self.image
                self.property.save(update_fields=['cover_image'])

        # If this is the first image, make it primary
        if not self.id and not PropertyImage.objects.filter(property=self.property).exists():
            self.is_primary = True

        super().save(*args, **kwargs)


class PropertyView(BaseModel):
    """Model for property views (e.g., street view, floor plan)"""
    VIEW_TYPES = [
        ('street', _('عرض الشارع')),
        ('satellite', _('عرض الأقمار الصناعية')),
        ('floor_plan', _('مخطط الطابق')),
        ('3d_model', _('نموذج ثلاثي الأبعاد')),
        ('virtual_tour', _('جولة افتراضية')),
    ]

    auction = models.ForeignKey(
        'Auction',
        on_delete=models.CASCADE,
        related_name='property_views',
        verbose_name=_('المزاد')
    )
    view_type = models.CharField(_('نوع العرض'), max_length=20, choices=VIEW_TYPES)

    # Location details
    location = models.JSONField(
        _('الموقع'),
        default=dict,
        blank=True,
        help_text=_('بيانات الموقع في التصور')
        # Example: {"latitude": 24.774265, "longitude": 46.738586, "floor": 2, "room": "غرفة المعيشة"}
    )

    # Physical details as JSON for better API structure
    dimensions = models.JSONField(
        _('الأبعاد'),
        default=dict,
        blank=True,
        help_text=_('تفاصيل الأبعاد والمساحة')
        # Example: {"width": 10, "length": 15, "height": 3, "size_sqm": 150, "elevation": 50}
    )

    # Keep some basic fields for backward compatibility
    address = models.CharField(_('العنوان'), max_length=255, blank=True)
    legal_description = models.TextField(_('الوصف القانوني'), blank=True)
    size_sqm = models.DecimalField(_('المساحة (متر مربع)'), max_digits=10, decimal_places=2, null=True, blank=True)
    elevation = models.DecimalField(_('الارتفاع'), max_digits=8, decimal_places=2, null=True, blank=True)

    # Media content
    image = models.ImageField(
        _('الصورة'),
        upload_to='properties/views/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ]
    )
    file = models.FileField(
        _('الملف'),
        upload_to='properties/views/files/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(['pdf', 'dwg', 'dxf', 'svg']),
        ],
        help_text=_('تحميل مخططات الطوابق، ملفات CAD، إلخ.')
    )

    # For 3D models or virtual tours
    external_url = models.URLField(_('رابط خارجي'), blank=True, help_text=_('رابط للنموذج ثلاثي الأبعاد أو الجولة الافتراضية'))
    embed_code = models.TextField(_('كود التضمين'), blank=True, help_text=_('كود HTML لتضمين الجولة الافتراضية'))

    # Additional configuration for the view
    view_config = models.JSONField(
        _('إعدادات العرض'),
        default=dict,
        blank=True,
        help_text=_('إعدادات وتكوين العرض')
        # Example: {"camera_position": {"x": 0, "y": 1.5, "z": 0}, "lighting": "natural", "render_quality": "high"}
    )

    class Meta:
        verbose_name = _('عرض العقار')
        verbose_name_plural = _('عروض العقار')
        ordering = ['view_type']

    def __str__(self):
        return f"{self.get_view_type_display()} للمزاد {self.auction}"


# -------------------------------------------------------------------------
# Auction Models
# -------------------------------------------------------------------------

class Auction(BaseModel):
    """Model for property auctions"""
    AUCTION_TYPES = [
        ('english', _('مزاد إنجليزي')),
        ('dutch', _('مزاد هولندي')),
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
    uuid = models.UUIDField(_('معرف فريد'), default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(_('العنوان'), max_length=255)
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
        # Example: [{"date": "2023-01-15", "from": "10:00", "to": "16:00", "notes": "بحضور الوكيل"}, ...]
    )

    # Auction schedule and timeline
    timeline = models.JSONField(
        _('الجدول الزمني'),
        default=list,
        blank=True,
        help_text=_('مراحل المزاد المختلفة وتواريخها')
        # Example: [{"phase": "التسجيل", "start": "2023-01-01", "end": "2023-01-10", "description": "فتح التسجيل للمزايدين"}, ...]
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
        # This will be updated automatically by signals
    )

    # Financial terms as JSON for better API structure
    financial_terms = models.JSONField(
        _('الشروط المالية'),
        default=dict,
        blank=True,
        help_text=_('تفاصيل وشروط الدفع والرسوم')
        # Example: {"buyer_premium": {"percentage": 2.5, "min": 1000}, "deposit": {"amount": 5000, "refundable": true}}
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
    cover_image = models.ImageField(
        _('صورة الغلاف'),
        upload_to='auctions/covers/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ]
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
        # Example: {"daily_views": {"2023-01-01": 150, "2023-01-02": 210}, "bidder_demographics": {"regions": {"الرياض": 60%, "جدة": 25%}}}
    )

    class Meta:
        verbose_name = _('مزاد')
        verbose_name_plural = _('المزادات')
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['is_published', 'is_featured']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # If using related_property's cover image when none is set
        if not self.cover_image and self.related_property and self.related_property.cover_image:
            self.cover_image = self.related_property.cover_image

        super().save(*args, **kwargs)


class AuctionImage(BaseImageModel):
    """Model for auction-specific images"""
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('المزاد')
    )
    image = models.ImageField(
        _('الصورة'),
        upload_to=auction_image_path,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ]
    )
    is_primary = models.BooleanField(_('صورة رئيسية'), default=False)
    caption = models.CharField(_('التعليق'), max_length=255, blank=True)
    order = models.PositiveIntegerField(_('ترتيب العرض'), default=0)

    # Additional metadata for the image
    metadata = models.JSONField(
        _('بيانات وصفية'),
        default=dict,
        blank=True
    )

    class Meta:
        verbose_name = _('صورة المزاد')
        verbose_name_plural = _('صور المزاد')
        ordering = ['order', '-is_primary', 'id']

    def __str__(self):
        return f"صورة للمزاد {self.auction.title} ({self.id})"

    def save(self, *args, **kwargs):
        # If this is marked as primary, unmark other primary images
        if self.is_primary:
            AuctionImage.objects.filter(
                auction=self.auction,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)

            # Also update the auction's cover image
            if self.auction and self.image:
                self.auction.cover_image = self.image
                self.auction.save(update_fields=['cover_image'])

        # If this is the first image, make it primary
        if not self.id and not AuctionImage.objects.filter(auction=self.auction).exists():
            self.is_primary = True

        super().save(*args, **kwargs)


class Bid(BaseModel):
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

class Document(BaseModel):
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
    file = models.FileField(
        _('ملف الوثيقة'),
        upload_to=document_file_path,
        validators=[
            FileExtensionValidator(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']),
        ],
        help_text=_('تحميل ملف الوثيقة (PDF، Word، أو صور)')
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
        if self.file and hasattr(self.file, 'file'):
            # Get file size in KB
            if hasattr(self.file, 'size'):
                self.file_size = self.file.size // 1024

            # Set content type
            file_name = self.file.name.lower()
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
                    img = Image.open(self.file)

                    # Create thumbnail
                    img.thumbnail((200, 200))

                    # Save thumbnail
                    thumb_io = BytesIO()
                    img_format = 'JPEG'
                    img.save(thumb_io, format=img_format, quality=70)

                    # Save to thumbnail field
                    thumb_name = f"{os.path.splitext(os.path.basename(self.file.name))[0]}_thumb.jpg"
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

class Contract(BaseModel):
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
    contract_file = models.FileField(
        _('ملف العقد'),
        upload_to=contract_file_path,
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(['pdf', 'doc', 'docx']),
        ],
        help_text=_('تحميل وثيقة العقد (PDF أو Word)')
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

class Notification(BaseModel):
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
