from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
from django.db.models import Max, Sum
import uuid
from datetime import timedelta
import logging
from django.utils.text import slugify
import random
import string
import json
import re

# Import CustomUser and Role from accounts app
from accounts.models import CustomUser, Role

# Configure logger
logger = logging.getLogger(__name__)

# Mixin for handling JSON fields
class JsonFieldMixin:
    """
    Mixin to handle JSON fields stored as TextField for SQLite compatibility.
    """
    def get_json_field(self, field_name, default=None):
        """Get a JSON field as a dictionary or list"""
        value = getattr(self, field_name, None)
        if not value:
            return default if default is not None else (
                [] if field_name in ['images', 'videos', 'features', 'amenities', 'files', 'attachments'] else {}
            )
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default if default is not None else (
                [] if field_name in ['images', 'videos', 'features', 'amenities', 'files', 'attachments'] else {}
            )

    def set_json_field(self, field_name, value):
        """Set a JSON field from a dictionary or list"""
        if value is not None:
            setattr(self, field_name, json.dumps(value))
        else:
            setattr(self, field_name, None)

# Arabic Slugify Function
def arabic_slugify(text):
    """
    Custom slugify function that preserves Arabic characters.
    Replaces spaces and special characters with hyphens.
    """
    if not text:
        return ""
    text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text).strip('-')
    text = re.sub(r'-+', '-', text)
    return text

# Status Transition Mixin Class
class StatusTransitionMixin:
    """
    Mixin to handle status transitions with validation.
    """
    def validate_status_transition(self, old_status, new_status, transitions_map, skip_validation=False):
        """
        Validate if a status transition from old_status to new_status is allowed.
        """
        if old_status != new_status:
            valid_transitions = transitions_map.get(old_status, [])
            if new_status not in valid_transitions and not skip_validation:
                raise ValidationError(f"Invalid status transition from '{old_status}' to '{new_status}'")
        return True

class BaseModel(models.Model):
    """
    Abstract base model with common fields for timestamps.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Override save to log model changes"""
        logger.debug(f"حفظ {self.__class__.__name__} مع المعرف: {self.pk}")
        super().save(*args, **kwargs)

# PROPERTY MODEL
class Property(BaseModel, StatusTransitionMixin, JsonFieldMixin):
    """
    Property model representing real estate listings with comprehensive
    features for effective property management.
    """
    PROPERTY_TYPES = [
        ('land', _('أرض')),
        ('apartment', _('شقة')),
        ('villa', _('فيلا')),
        ('commercial', _('تجاري')),
        ('building', _('مبنى')),
        ('farm', _('مزرعة')),
        ('industrial', _('صناعي')),
        ('office', _('مكتب')),
        ('retail', _('محل تجاري')),
        ('mixed_use', _('متعدد الاستخدامات')),
    ]

    PROPERTY_STATUS = [
        ('draft', _('مسودة')),
        ('pending_approval', _('في انتظار الموافقة')),
        ('active', _('نشط')),
        ('under_contract', _('تحت التعاقد')),
        ('sold', _('مباع')),
        ('inactive', _('غير نشط')),
        ('rejected', _('مرفوض')),
    ]

    PROPERTY_CONDITION = [
        ('excellent', _('ممتاز')),
        ('very_good', _('جيد جدا')),
        ('good', _('جيد')),
        ('fair', _('مقبول')),
        ('poor', _('سيئ')),
        ('under_construction', _('تحت الإنشاء')),
        ('new', _('جديد')),
    ]

    FACING_DIRECTIONS = [
        ('north', _('شمال')),
        ('east', _('شرق')),
        ('south', _('جنوب')),
        ('west', _('غرب')),
        ('northeast', _('شمال شرق')),
        ('southeast', _('جنوب شرق')),
        ('southwest', _('جنوب غرب')),
        ('northwest', _('شمال غرب')),
    ]

    USAGE_TYPES = [
        ('residential', _('سكني')),
        ('commercial', _('تجاري')),
        ('mixed', _('مختلط')),
        ('industrial', _('صناعي')),
        ('agricultural', _('زراعي')),
    ]

    STATUS_TRANSITIONS = {
        'draft': ['pending_approval', 'inactive', 'rejected'],
        'pending_approval': ['active', 'rejected', 'inactive'],
        'active': ['under_contract', 'sold', 'inactive'],
        'under_contract': ['sold', 'active', 'inactive'],
        'sold': ['inactive'],  # Consider allowing 'active' if sold properties can be reactivated
        'inactive': ['draft', 'active'],
        'rejected': ['draft', 'inactive'],
    }

    # Basic information
    property_number = models.CharField(max_length=50, unique=True, verbose_name=_('رقم العقار'))
    title = models.CharField(max_length=255, verbose_name=_('عنوان العقار'))
    slug = models.CharField(max_length=255, unique=True, blank=True, verbose_name=_('الرابط المختصر'))
    property_type = models.CharField(
        max_length=50,
        choices=PROPERTY_TYPES,
        verbose_name=_('نوع العقار')
    )
    description = models.TextField(blank=True, null=True, verbose_name=_('وصف تفصيلي'))
    condition = models.CharField(
        max_length=50,
        choices=PROPERTY_CONDITION,
        default='good',
        verbose_name=_('حالة العقار')
    )

    # Ownership details
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,  # Changed to SET_NULL to allow property persistence
        null=True,
        related_name='owned_properties',
        verbose_name=_('المالك')
    )
    status = models.CharField(
        max_length=20,
        choices=PROPERTY_STATUS,
        default='draft',
        verbose_name=_('حالة العقار')
    )
    status_history = models.TextField(blank=True, null=True, verbose_name=_('سجل حالات العقار'))
    deed_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('رقم الصك'))
    deed_date = models.DateField(blank=True, null=True, verbose_name=_('تاريخ الصك'))

    # Location information
    address = models.CharField(max_length=255, verbose_name=_('العنوان'))
    city = models.CharField(max_length=100, verbose_name=_('المدينة'))
    district = models.CharField(max_length=100, verbose_name=_('الحي'))
    postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('الرمز البريدي'))
    country = models.CharField(max_length=100, default='Saudi Arabia', verbose_name=_('الدولة'))
    location = models.TextField(blank=True, null=True, verbose_name=_('الموقع الجغرافي'))
    facing_direction = models.CharField(
        max_length=20,
        choices=FACING_DIRECTIONS,
        blank=True,
        null=True,
        verbose_name=_('اتجاه الواجهة')
    )
    street_details = models.TextField(blank=True, null=True, verbose_name=_('تفاصيل الشوارع'))

    # Property specifications
    area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('مساحة العقار')
    )
    built_up_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        blank=True,
        null=True,
        verbose_name=_('المساحة المبنية')
    )
    bedrooms = models.PositiveIntegerField(default=0, verbose_name=_('عدد غرف النوم'))
    bathrooms = models.PositiveIntegerField(default=0, verbose_name=_('عدد الحمامات'))
    rooms = models.TextField(blank=True, null=True, verbose_name=_('تفاصيل الغرف'), default='[]')
    floor_number = models.PositiveIntegerField(blank=True, null=True, verbose_name=_('رقم الطابق'))
    total_floors = models.PositiveIntegerField(blank=True, null=True, verbose_name=_('إجمالي الطوابق'))
    year_built = models.PositiveIntegerField(blank=True, null=True, verbose_name=_('سنة البناء'))

    # Balconies and outdoor spaces
    outdoor_spaces = models.TextField(blank=True, null=True, verbose_name=_('المساحات الخارجية'))

    # Financial details
    estimated_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('القيمة التقديرية')
    )
    asking_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        blank=True,
        null=True,
        verbose_name=_('السعر المطلوب')
    )
    price_per_sqm = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        blank=True,
        null=True,
        verbose_name=_('السعر لكل متر مربع')
    )
    rental_details = models.TextField(blank=True, null=True, verbose_name=_('تفاصيل الإيجار'))

    # Parking details
    parking = models.TextField(blank=True, null=True, verbose_name=_('تفاصيل مواقف السيارات'))

    # Media files
    images = models.TextField(blank=True, null=True, verbose_name=_('صور العقار'))
    videos = models.TextField(blank=True, null=True, verbose_name=_('فيديوهات العقار'))
    virtual_tours = models.TextField(blank=True, null=True, verbose_name=_('جولات افتراضية'))
    documents = models.TextField(blank=True, null=True, verbose_name=_('مستندات العقار'))
    floor_plans = models.TextField(blank=True, null=True, verbose_name=_('مخططات الطوابق'))

    # Features and amenities
    features = models.TextField(blank=True, null=True, verbose_name=_('المميزات'))
    amenities = models.TextField(blank=True, null=True, verbose_name=_('المرافق'))

    # Building services and infrastructure
    building_services = models.TextField(blank=True, null=True, verbose_name=_('خدمات المبنى'))
    infrastructure = models.TextField(blank=True, null=True, verbose_name=_('البنية التحتية'))

    # Current and potential usage
    current_usage = models.CharField(
        max_length=30,
        choices=USAGE_TYPES,
        blank=True,
        null=True,
        verbose_name=_('الاستخدام الحالي')
    )
    optimal_usage = models.CharField(
        max_length=30,
        choices=USAGE_TYPES,
        blank=True,
        null=True,
        verbose_name=_('الاستخدام الأمثل')
    )

    # Surrounding landmarks and services
    surroundings = models.TextField(blank=True, null=True, verbose_name=_('المحيط'))

    # Verification and approvals
    is_verified = models.BooleanField(default=False, verbose_name=_('تم التحقق'))
    verified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_properties',
        verbose_name=_('تم التحقق بواسطة')
    )
    verification_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ التحقق'))
    verification_details = models.TextField(blank=True, null=True, verbose_name=_('تفاصيل التحقق'))

    # Auction and visibility settings
    is_featured = models.BooleanField(default=False, verbose_name=_('مميز'))
    is_published = models.BooleanField(default=False, verbose_name=_('منشور'))
    publish_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ النشر'))
    views_count = models.PositiveIntegerField(default=0, verbose_name=_('عدد المشاهدات'))

    # Administrative
    reference_ids = models.TextField(blank=True, null=True, verbose_name=_('أرقام مرجعية'))

    class Meta:
        db_table = 'properties'
        verbose_name = _('عقار')
        verbose_name_plural = _('العقارات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property_type']),
            models.Index(fields=['city', 'district']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured', 'is_published']),
            models.Index(fields=['year_built']),
            models.Index(fields=['area']),
            models.Index(fields=['estimated_value']),
            models.Index(fields=['bedrooms', 'bathrooms']),
            models.Index(fields=['owner']),
            models.Index(fields=['property_number']),
            models.Index(fields=['slug']),
            models.Index(fields=['condition']),
            models.Index(fields=['current_usage']),
            models.Index(fields=['optimal_usage']),
            models.Index(fields=['verified_by']),
            models.Index(fields=['created_at', 'updated_at']),
        ]

    def __str__(self):
        return f"{self.property_number} - {self.title}"

    def generate_unique_slug(self):
        """Generate a unique slug with retry limit"""
        base_slug = arabic_slugify(self.title) or arabic_slugify(self.property_number)
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        max_retries = 10
        attempt = 0

        while attempt < max_retries:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            unique_slug = f"{base_slug}-{timestamp}-{random_suffix}"
            if not Property.objects.filter(slug=unique_slug).exists():
                return unique_slug
            attempt += 1

        raise ValueError(f"Unable to generate a unique slug for '{self.title}' after {max_retries} attempts")

    def clean(self):
        """Validate model data before saving"""
        if self.pk:
            try:
                original = Property.objects.get(pk=self.pk)
                if original.status != self.status:
                    self.validate_status_transition(
                        original.status,
                        self.status,
                        self.STATUS_TRANSITIONS
                    )
            except Property.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        """Save the property with proper validation and side effects"""
        skip_validation = kwargs.pop('skip_validation', False)
        user = kwargs.pop('user', None)

        if not self.property_number:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_suffix = ''.join(random.choices(string.digits, k=4))
            self.property_number = f"PROP-{timestamp}-{random_suffix}"

        if not self.slug:
            self.slug = self.generate_unique_slug()

        if self.is_published and not self.publish_date:
            self.publish_date = timezone.now()

        if self.estimated_value and self.area and not self.price_per_sqm:
            try:
                self.price_per_sqm = self.estimated_value / self.area
            except (TypeError, ValueError):
                self.price_per_sqm = 0

        original_status = None
        if self.pk:
            try:
                original = Property.objects.get(pk=self.pk)
                original_status = original.status
            except Property.DoesNotExist:
                pass

        if original_status and original_status != self.status and not skip_validation:
            self.validate_status_transition(
                original_status,
                self.status,
                self.STATUS_TRANSITIONS
            )

            history_data = self.get_json_field('status_history', []) or []
            history_data.append({
                'status': self.status,
                'previous_status': original_status,
                'date': timezone.now().isoformat(),
                'user': getattr(user, 'id', None)
            })
            self.set_json_field('status_history', history_data)

        super().save(*args, **kwargs)

    @property
    def location_dict(self):
        return self.get_json_field('location')

    @location_dict.setter
    def location_dict(self, value):
        self.set_json_field('location', value)

    @property
    def main_image_url(self):
        images = self.get_json_field('images')
        if not images:
            return None
        for img in images:
            if img.get('is_primary'):
                return img.get('path')
        return images[0].get('path') if images else None

    @property
    def has_auction(self):
        return self.auctions.filter(status__in=['draft', 'pending', 'active']).exists()

    def recommended_properties(self, limit=5):
        return Property.objects.filter(
            property_type=self.property_type,
            city=self.city,
            is_published=True
        ).exclude(pk=self.pk).filter(
            area__range=(self.area * 0.8, self.area * 1.2)
        ).order_by('-is_featured', '-views_count')[:limit]

    @property
    def location_coordinates(self):
        location_data = self.get_json_field('location')
        if location_data and 'latitude' in location_data and 'longitude' in location_data:
            return {
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude')
            }
        return None

# AUCTION MODEL
class Auction(BaseModel, StatusTransitionMixin, JsonFieldMixin):
    """Auction model for property auctions"""
    AUCTION_STATUS = [
        ('draft', _('مسودة')),
        ('pending', _('قيد الانتظار')),
        ('active', _('مفتوح')),
        ('extended', _('ممدد')),
        ('closed', _('مغلق')),
        ('sold', _('مُباع')),
        ('cancelled', _('ملغي')),
    ]

    AUCTION_TYPES = [
        ('public', _('عام')),
        ('private', _('خاص')),
        ('online', _('إلكتروني')),
        ('onsite', _('حضوري')),
        ('hybrid', _('مختلط')),
    ]

    STATUS_TRANSITIONS = {
        'draft': ['pending', 'cancelled'],
        'pending': ['active', 'cancelled'],
        'active': ['extended', 'closed', 'cancelled'],
        'extended': ['closed', 'cancelled'],
        'closed': ['sold', 'cancelled'],  # Added transitions for flexibility
        'sold': ['cancelled'],  # Allow cancellation of sold status if needed
        'cancelled': []
    }

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_('المعرف العالمي'))
    related_property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,  # Prevents property deletion during active auctions
        related_name='auctions',
        verbose_name=_('العقار')
    )
    title = models.CharField(max_length=255, verbose_name=_('عنوان المزاد'))
    slug = models.CharField(max_length=255, unique=True, verbose_name=_('الرابط المختصر'))
    description = models.TextField(blank=True, null=True, verbose_name=_('وصف المزاد'))

    auction_type = models.CharField(
        max_length=50,
        choices=AUCTION_TYPES,
        default='online',
        verbose_name=_('نوع المزاد')
    )
    status = models.CharField(
        max_length=20,
        choices=AUCTION_STATUS,
        default='draft',
        verbose_name=_('حالة المزاد')
    )

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_auctions',
        verbose_name=_('تم الإنشاء بواسطة')
    )
    auctioneer = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_auctions',
        verbose_name=_('منظم المزاد')
    )

    start_date = models.DateTimeField(verbose_name=_('تاريخ بدء المزاد'))
    end_date = models.DateTimeField(verbose_name=_('تاريخ انتهاء المزاد'))
    auto_extend = models.BooleanField(default=True, verbose_name=_('تمديد تلقائي'))
    extension_minutes = models.PositiveIntegerField(default=10, verbose_name=_('دقائق التمديد'))

    starting_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('سعر البدء')
    )
    reserve_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('السعر الاحتياطي')
    )
    min_bid_increment = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=100,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('الحد الأدنى للزيادة')
    )
    deposit_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        blank=True,
        null=True,
        verbose_name=_('مبلغ التأمين')
    )
    deposit_required = models.BooleanField(default=False, verbose_name=_('مطلوب تأمين'))

    buyer_premium_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.0,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('نسبة عمولة المشتري')
    )
    seller_commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.5,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('نسبة عمولة البائع')
    )

    current_bid = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('المزايدة الحالية')
    )
    winning_bid = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('المزايدة الفائزة')
    )
    winning_bidder = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_auctions',
        verbose_name=_('المزايد الفائز')
    )
    end_reason = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('سبب الإنهاء'))

    location_address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('عنوان الموقع'))
    location = models.TextField(blank=True, null=True, verbose_name=_('الموقع الجغرافي'))
    location_details = models.TextField(blank=True, null=True, verbose_name=_('تفاصيل الموقع'))

    terms_conditions = models.TextField(blank=True, null=True, verbose_name=_('الشروط والأحكام'))
    participation_requirements = models.TextField(blank=True, null=True, verbose_name=_('متطلبات المشاركة'))

    images = models.TextField(blank=True, null=True, verbose_name=_('صور المزاد'))
    videos = models.TextField(blank=True, null=True, verbose_name=_('فيديوهات المزاد'))
    documents = models.TextField(blank=True, null=True, verbose_name=_('مستندات المزاد'))

    is_private = models.BooleanField(default=False, verbose_name=_('مزاد خاص'))
    invited_bidders = models.ManyToManyField(
        CustomUser,
        related_name='invited_auctions',
        blank=True,
        verbose_name=_('المزايدين المدعوين')
    )

    is_featured = models.BooleanField(default=False, verbose_name=_('مزاد مميز'))
    is_published = models.BooleanField(default=False, verbose_name=_('منشور'))
    publish_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ النشر'))
    views_count = models.PositiveIntegerField(default=0, verbose_name=_('عدد المشاهدات'))

    class Meta:
        db_table = 'auctions'
        verbose_name = _('مزاد')
        verbose_name_plural = _('المزادات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['is_featured', 'is_published']),
            models.Index(fields=['uuid']),
            models.Index(fields=['slug']),
            models.Index(fields=['related_property']),
            models.Index(fields=['created_by']),
            models.Index(fields=['auctioneer']),
            models.Index(fields=['winning_bidder']),
            models.Index(fields=['auction_type']),
            models.Index(fields=['created_at', 'updated_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def generate_unique_slug(self):
        """Generate a unique slug with retry limit"""
        base_slug = arabic_slugify(self.title) or str(self.uuid)[:8]
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        max_retries = 10
        attempt = 0

        while attempt < max_retries:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            unique_slug = f"{base_slug}-{timestamp}-{random_suffix}"
            if not Auction.objects.filter(slug=unique_slug).exists():
                return unique_slug
            attempt += 1

        raise ValueError(f"Unable to generate a unique slug for '{self.title}' after {max_retries} attempts")

    def clean(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError(_('تاريخ انتهاء المزاد يجب أن يكون بعد تاريخ البدء'))

        if self.pk:
            try:
                original = Auction.objects.get(pk=self.pk)
                if original.status != self.status:
                    self.validate_status_transition(
                        original.status,
                        self.status,
                        self.STATUS_TRANSITIONS
                    )
            except Auction.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        skip_validation = kwargs.pop('skip_validation', False)

        if not self.slug:
            self.slug = self.generate_unique_slug()

        if self.is_published and not self.publish_date:
            self.publish_date = timezone.now()

        original_status = None
        if self.pk:
            try:
                original = Auction.objects.get(pk=self.pk)
                original_status = original.status
            except Auction.DoesNotExist:
                pass

        if original_status and original_status != self.status and not skip_validation:
            self.validate_status_transition(
                original_status,
                self.status,
                self.STATUS_TRANSITIONS
            )

        super().save(*args, **kwargs)

    @property
    def location_dict(self):
        return self.get_json_field('location')

    @location_dict.setter
    def location_dict(self, value):
        self.set_json_field('location', value)

    @property
    def highest_bid(self):
        highest = self.bids.aggregate(Max('bid_amount'))['bid_amount__max']
        return highest if highest is not None else self.starting_price

    @property
    def bid_count(self):
        return self.bids.count()

    @property
    def unique_bidders_count(self):
        return self.bids.values('bidder').distinct().count()

    @property
    def time_remaining(self):
        if self.status != 'active':
            return 0
        now = timezone.now()
        if now > self.end_date:
            return 0
        return (self.end_date - now).total_seconds()

    @property
    def is_active(self):
        if self.status != 'active':
            return False
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    @property
    def featured_image_url(self):
        images = self.get_json_field('images')
        if not images:
            return self.related_property.main_image_url
        for img in images:
            if img.get('is_featured'):
                return img.get('path')
        return images[0].get('path') if images else self.related_property.main_image_url

    @property
    def location_coordinates(self):
        location_data = self.get_json_field('location')
        if location_data and 'latitude' in location_data and 'longitude' in location_data:
            return {
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude')
            }
        return None

    def extend_auction(self, minutes=None):
        if not minutes:
            minutes = self.extension_minutes
        self.end_date = self.end_date + timedelta(minutes=minutes)
        self.status = 'extended'
        self.save(update_fields=['end_date', 'status', 'updated_at'])
        return True

class Bid(BaseModel, JsonFieldMixin):
    """Model for auction bids"""
    BID_STATUS = [
        ('pending', _('معلق')),
        ('accepted', _('مقبول')),
        ('rejected', _('مرفوض')),
        ('winning', _('فائز')),
        ('outbid', _('تم تجاوزه')),
        ('cancelled', _('ملغي')),
    ]

    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name=_('المزاد')
    )
    bidder = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,  # Preserve bid history
        null=True,
        related_name='bids',
        verbose_name=_('المزايد')
    )
    bid_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('قيمة العطاء')
    )
    bid_time = models.DateTimeField(auto_now_add=True, verbose_name=_('وقت تقديم العطاء'))
    status = models.CharField(
        max_length=20,
        choices=BID_STATUS,
        default='pending',
        verbose_name=_('حالة العطاء')
    )

    max_bid_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        blank=True,
        null=True,
        verbose_name=_('الحد الأقصى للمزايدة التلقائية')
    )
    is_auto_bid = models.BooleanField(default=False, verbose_name=_('مزايدة تلقائية'))

    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name=_('عنوان IP'))
    user_agent = models.TextField(blank=True, null=True, verbose_name=_('معلومات المتصفح'))
    device_info = models.TextField(default='{}', blank=True, null=True, verbose_name=_('معلومات الجهاز'))

    notes = models.TextField(blank=True, null=True, verbose_name=_('ملاحظات'))

    class Meta:
        db_table = 'bids'
        verbose_name = _('عطاء')
        verbose_name_plural = _('العطاءات')
        ordering = ['-bid_amount', 'bid_time']
        indexes = [
            models.Index(fields=['auction', 'bid_amount']),
            models.Index(fields=['auction', 'bidder']),
            models.Index(fields=['status']),
            models.Index(fields=['bidder']),
            models.Index(fields=['bid_time']),
            models.Index(fields=['is_auto_bid']),
            models.Index(fields=['max_bid_amount']),
            models.Index(fields=['created_at', 'updated_at']),
            models.Index(fields=['auction', 'status', 'bid_amount']),
        ]

    def __str__(self):
        return f"{self.bid_amount} من {self.bidder} للمزاد {self.auction.title}"

    def clean(self):
        if self.auction.status != 'active':
            raise ValidationError(_('لا يمكن تقديم عطاء على مزاد غير نشط'))
        now = timezone.now()
        if now < self.auction.start_date:
            raise ValidationError(_('لم يبدأ المزاد بعد'))
        if now > self.auction.end_date:
            raise ValidationError(_('انتهى المزاد بالفعل'))
        highest_bid = self.auction.highest_bid
        min_bid = highest_bid + self.auction.min_bid_increment
        if self.bid_amount < min_bid:
            raise ValidationError(f"يجب أن يكون مبلغ المزايدة {min_bid} على الأقل")

    def save(self, *args, **kwargs):
        skip_validation = kwargs.pop('skip_validation', False)

        if not self.pk and not self.bid_time:
            self.bid_time = timezone.now()

        if not self.pk and not skip_validation:
            auction = self.auction
            if auction.status != 'active':
                raise ValidationError(_('لا يمكن تقديم عطاء على مزاد غير نشط'))
            now = timezone.now()
            if now < auction.start_date:
                raise ValidationError(_('لم يبدأ المزاد بعد'))
            if now > auction.end_date:
                raise ValidationError(_('انتهى المزاد بالفعل'))
            highest_bid = auction.highest_bid
            min_bid = highest_bid + auction.min_bid_increment
            if self.bid_amount < min_bid:
                raise ValidationError(f"يجب أن يكون مبلغ المزايدة {min_bid} على الأقل")

        if isinstance(self.device_info, dict):
            self.device_info = json.dumps(self.device_info)

        super().save(*args, **kwargs)

        if self.pk and self.status in ['pending', 'accepted']:
            self.auction.current_bid = self.bid_amount
            self.auction.save(update_fields=['current_bid', 'updated_at'])

            previous_winning = Bid.objects.filter(
                auction=self.auction,
                status='winning'
            ).first()
            if previous_winning:
                previous_winning.status = 'outbid'
                previous_winning.save(update_fields=['status', 'updated_at'])

            if (self.auction.auto_extend and
                self.auction.end_date - now <= timedelta(minutes=self.auction.extension_minutes)):
                self.auction.extend_auction()

    def mark_as_winning(self):
        try:
            self.status = 'winning'
            self.save(update_fields=['status', 'updated_at'])
            self.auction.winning_bid = self.bid_amount
            self.auction.winning_bidder = self.bidder
            self.auction.save(update_fields=['winning_bid', 'winning_bidder', 'updated_at'])
            return True
        except Exception as e:
            logger.error(f"Error marking bid as winning: {str(e)}")
            return False

class Document(BaseModel, StatusTransitionMixin, JsonFieldMixin):
    """Model for property and auction related documents"""
    DOCUMENT_TYPES = [
        ('deed', _('صك ملكية')),
        ('inspection', _('تقرير فحص')),
        ('appraisal', _('تقرير تقييم')),
        ('coastal_assessment', _('تقييم ساحلي')),
        ('legal', _('مستند قانوني')),
        ('contract', _('عقد')),
        ('identity', _('إثبات هوية')),
        ('financial', _('مستند مالي')),
        ('other', _('أخرى')),
    ]

    VERIFICATION_STATUS = [
        ('pending', _('معلق')),
        ('verified', _('تم التحقق')),
        ('rejected', _('مرفوض')),
    ]

    STATUS_TRANSITIONS = {
        'pending': ['verified', 'rejected'],
        'verified': ['pending', 'rejected'],
        'rejected': ['pending'],
    }

    document_number = models.CharField(max_length=50, unique=True, verbose_name=_('رقم المستند'))
    title = models.CharField(max_length=255, verbose_name=_('عنوان المستند'))
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, verbose_name=_('نوع المستند'))
    description = models.TextField(blank=True, null=True, verbose_name=_('وصف المستند'))

    related_property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='property_documents',
        verbose_name=_('العقار المرتبط')
    )
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='auction_documents',
        verbose_name=_('المزاد المرتبط')
    )
    contract = models.ForeignKey(
        'Contract',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='contract_documents',
        verbose_name=_('العقد المرتبط')
    )

    files = models.TextField(default='[]', blank=True, null=True, verbose_name=_('ملفات المستند'))

    uploaded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents',
        verbose_name=_('تم الرفع بواسطة')
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending',
        verbose_name=_('حالة التحقق')
    )
    verified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents',
        verbose_name=_('تم التحقق بواسطة')
    )
    verification_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ التحقق'))
    verification_notes = models.TextField(blank=True, null=True, verbose_name=_('ملاحظات التحقق'))

    metadata = models.TextField(default='{}', blank=True, null=True, verbose_name=_('بيانات وصفية'))

    issue_date = models.DateField(blank=True, null=True, verbose_name=_('تاريخ الإصدار'))
    expiry_date = models.DateField(blank=True, null=True, verbose_name=_('تاريخ الانتهاء'))

    class Meta:
        db_table = 'documents'
        verbose_name = _('مستند')
        verbose_name_plural = _('المستندات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['document_type']),
            models.Index(fields=['related_property']),
            models.Index(fields=['auction']),
            models.Index(fields=['contract']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['verified_by']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['created_at', 'updated_at']),
        ]

    def __str__(self):
        return f"{self.get_document_type_display()}: {self.title}"

    def clean(self):
        if not self.related_property and not self.auction and not self.contract:
            raise ValidationError(_('يجب تحديد العقار أو المزاد أو العقد المرتبط'))
        if self.pk:
            try:
                original = Document.objects.get(pk=self.pk)
                if original.verification_status != self.verification_status:
                    self.validate_status_transition(
                        original.verification_status,
                        self.verification_status,
                        self.STATUS_TRANSITIONS
                    )
            except Document.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        if self.verification_status == 'verified' and not self.verification_date and self.verified_by:
            self.verification_date = timezone.now()
        if self.pk:
            try:
                original = Document.objects.get(pk=self.pk)
                if original.verification_status == 'verified' and self.verification_status != 'verified':
                    self.verification_date = None
            except Document.DoesNotExist:
                pass
        if isinstance(self.metadata, dict):
            self.metadata = json.dumps(self.metadata)
        if isinstance(self.files, list):
            self.files = json.dumps(self.files)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    @property
    def main_file_url(self):
        files = self.get_json_field('files')
        if not files:
            return None
        return files[0].get('path') if files else None

    def verify(self, user, notes=None):
        self.verification_status = 'verified'
        self.verified_by = user
        self.verification_date = timezone.now()
        if notes:
            self.verification_notes = notes
        self.save(update_fields=[
            'verification_status',
            'verified_by',
            'verification_date',
            'verification_notes',
            'updated_at'
        ])
        return True

class Contract(BaseModel, StatusTransitionMixin, JsonFieldMixin):
    """Contract model for auction sales contracts"""
    CONTRACT_STATUS = [
        ('draft', _('مسودة')),
        ('pending_review', _('قيد المراجعة')),
        ('pending_buyer', _('بانتظار المشتري')),
        ('pending_seller', _('بانتظار البائع')),
        ('pending_payment', _('بانتظار الدفع')),
        ('signed', _('موقع')),
        ('active', _('نشط')),
        ('completed', _('مكتمل')),
        ('cancelled', _('ملغى')),
        ('disputed', _('متنازع عليه')),
    ]

    PAYMENT_METHODS = [
        ('bank_transfer', _('تحويل بنكي')),
        ('cash', _('نقدي')),
        ('check', _('شيك')),
        ('installment', _('تقسيط')),
        ('escrow', _('ضمان')),
    ]

    STATUS_TRANSITIONS = {
        'draft': ['pending_review', 'pending_buyer', 'pending_seller', 'cancelled'],
        'pending_review': ['pending_buyer', 'pending_seller', 'cancelled', 'draft'],
        'pending_buyer': ['signed', 'pending_seller', 'cancelled', 'draft'],
        'pending_seller': ['signed', 'pending_buyer', 'cancelled', 'draft'],
        'pending_payment': ['active', 'signed', 'cancelled'],
        'signed': ['pending_payment', 'active', 'cancelled'],
        'active': ['completed', 'disputed', 'cancelled'],
        'completed': ['disputed'],
        'cancelled': [],
        'disputed': ['active', 'cancelled', 'completed'],
    }

    contract_number = models.CharField(max_length=50, unique=True, verbose_name=_('رقم العقد'))
    title = models.CharField(max_length=255, verbose_name=_('عنوان العقد'))

    auction = models.OneToOneField(
        Auction,
        on_delete=models.PROTECT,
        related_name='contract',
        verbose_name=_('المزاد')
    )
    related_property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name=_('العقار')
    )

    buyer = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='buyer_contracts',
        verbose_name=_('المشتري')
    )
    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='seller_contracts',
        verbose_name=_('البائع')
    )
    agent = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_contracts',
        verbose_name=_('الوكيل العقاري')
    )

    status = models.CharField(
        max_length=20,
        choices=CONTRACT_STATUS,
        default='draft',
        verbose_name=_('حالة العقد')
    )
    contract_date = models.DateField(verbose_name=_('تاريخ العقد'))
    effective_date = models.DateField(blank=True, null=True, verbose_name=_('تاريخ السريان'))
    expiry_date = models.DateField(blank=True, null=True, verbose_name=_('تاريخ الانتهاء'))

    contract_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('قيمة العقد')
    )
    deposit_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('قيمة العربون')
    )
    commission_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('قيمة العمولة')
    )
    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('قيمة الضريبة')
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('المبلغ الإجمالي')
    )
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, verbose_name=_('طريقة الدفع'))
    payment_terms = models.TextField(verbose_name=_('شروط الدفع'))

    files = models.TextField(default='[]', blank=True, null=True, verbose_name=_('ملفات العقد'))

    terms_conditions = models.TextField(blank=True, null=True, verbose_name=_('الشروط والأحكام'))
    special_conditions = models.TextField(blank=True, null=True, verbose_name=_('شروط خاصة'))
    notes = models.TextField(blank=True, null=True, verbose_name=_('ملاحظات'))

    buyer_signed = models.BooleanField(default=False, verbose_name=_('وقّع المشتري'))
    seller_signed = models.BooleanField(default=False, verbose_name=_('وقّع البائع'))
    agent_signed = models.BooleanField(default=False, verbose_name=_('وقّع الوكيل'))
    buyer_signature_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ توقيع المشتري'))
    seller_signature_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ توقيع البائع'))
    agent_signature_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ توقيع الوكيل'))

    is_verified = models.BooleanField(default=False, verbose_name=_('تم التحقق'))
    verification_authority = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('جهة التوثيق'))
    verification_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ التوثيق'))

    class Meta:
        db_table = 'contracts'
        verbose_name = _('عقد')
        verbose_name_plural = _('العقود')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['contract_date']),
            models.Index(fields=['buyer', 'seller']),
            models.Index(fields=['auction']),
            models.Index(fields=['related_property']),
            models.Index(fields=['agent']),
            models.Index(fields=['buyer']),
            models.Index(fields=['seller']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['contract_number']),
            models.Index(fields=['effective_date']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['buyer_signed', 'seller_signed', 'agent_signed']),
            models.Index(fields=['created_at', 'updated_at']),
        ]

    def __str__(self):
        return f"{self.contract_number} - {self.title}"

    def clean(self):
        if self.auction and self.related_property != self.auction.related_property:
            raise ValidationError(_('العقار يجب أن يكون هو نفس عقار المزاد'))
        if self.pk:
            try:
                original = Contract.objects.get(pk=self.pk)
                if original.status != self.status:
                    self.validate_status_transition(
                        original.status,
                        self.status,
                        self.STATUS_TRANSITIONS
                    )
            except Contract.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        if not self.total_amount or self.total_amount == 0:
            self.total_amount = (
                self.contract_amount +
                self.commission_amount +
                self.tax_amount
            )

        is_new = not self.pk
        if isinstance(self.files, list):
            self.files = json.dumps(self.files)

        if not is_new:
            if self.buyer_signed and self.seller_signed:
                if not self.agent or self.agent_signed:
                    if self.status in ['pending_buyer', 'pending_seller']:
                        self.status = 'signed'

        super().save(*args, **kwargs)

    @property
    def is_fully_signed(self):
        if not self.buyer_signed or not self.seller_signed:
            return False
        if self.agent and not self.agent_signed:
            return False
        return True

    @property
    def main_file_url(self):
        files = self.get_json_field('files')
        if not files:
            return None
        for file in files:
            if file.get('file_type') == 'contract':
                return file.get('path')
        return files[0].get('path') if files else None

    def sign_as_buyer(self, user=None):
        if user and user != self.buyer:
            raise ValidationError(_('المستخدم ليس هو المشتري'))
        self.buyer_signed = True
        self.buyer_signature_date = timezone.now()
        if self.seller_signed and (not self.agent or self.agent_signed):
            self.status = 'signed'
        else:
            self.status = 'pending_seller'
        self.save(update_fields=[
            'buyer_signed',
            'buyer_signature_date',
            'status',
            'updated_at'
        ])
        return True

    def sign_as_seller(self, user=None):
        if user and user != self.seller:
            raise ValidationError(_('المستخدم ليس هو البائع'))
        self.seller_signed = True
        self.seller_signature_date = timezone.now()
        if self.buyer_signed and (not self.agent or self.agent_signed):
            self.status = 'signed'
        else:
            self.status = 'pending_buyer'
        self.save(update_fields=[
            'seller_signed',
            'seller_signature_date',
            'status',
            'updated_at'
        ])
        return True

class Payment(BaseModel, StatusTransitionMixin, JsonFieldMixin):
    """Payment model for contract payments"""
    PAYMENT_STATUS = [
        ('pending', _('معلق')),
        ('processing', _('قيد المعالجة')),
        ('completed', _('مكتمل')),
        ('failed', _('فاشل')),
        ('refunded', _('مسترد')),
        ('cancelled', _('ملغى')),
        ('disputed', _('متنازع عليه')),
    ]

    PAYMENT_TYPES = [
        ('deposit', _('عربون')),
        ('installment', _('قسط')),
        ('full_payment', _('دفعة كاملة')),
        ('commission', _('عمولة')),
        ('tax', _('ضريبة')),
        ('fee', _('رسوم')),
    ]

    PAYMENT_METHODS = [
        ('bank_transfer', _('تحويل بنكي')),
        ('cash', _('نقدي')),
        ('check', _('شيك')),
        ('credit_card', _('بطاقة ائتمان')),
        ('online', _('دفع إلكتروني')),
    ]

    STATUS_TRANSITIONS = {
        'pending': ['processing', 'completed', 'failed', 'cancelled'],
        'processing': ['completed', 'failed', 'cancelled'],
        'completed': ['refunded', 'disputed'],
        'failed': ['pending', 'cancelled'],
        'refunded': ['disputed'],
        'cancelled': [],
        'disputed': ['completed', 'refunded', 'cancelled'],
    }

    payment_number = models.CharField(max_length=50, unique=True, verbose_name=_('رقم الدفعة'))

    contract = models.ForeignKey(
        Contract,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_('العقد')
    )
    payer = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='payments_made',
        verbose_name=_('الدافع')
    )
    payee = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='payments_received',
        verbose_name=_('المستلم')
    )

    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, verbose_name=_('نوع الدفعة'))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name=_('طريقة الدفع'))
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('المبلغ')
    )
    currency = models.CharField(max_length=3, default='SAR', verbose_name=_('العملة'))
    payment_date = models.DateTimeField(verbose_name=_('تاريخ الدفع'))
    due_date = models.DateField(blank=True, null=True, verbose_name=_('تاريخ الاستحقاق'))

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending',
        verbose_name=_('حالة الدفعة')
    )
    confirmed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ التأكيد'))
    confirmed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_payments',
        verbose_name=_('تم التأكيد بواسطة')
    )

    transaction_reference = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('مرجع المعاملة'))
    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('اسم البنك'))
    account_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('اسم الحساب'))
    account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('رقم الحساب'))
    check_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('رقم الشيك'))

    files = models.TextField(default='[]', blank=True, null=True, verbose_name=_('ملفات الدفعة'))
    notes = models.TextField(blank=True, null=True, verbose_name=_('ملاحظات'))

    class Meta:
        db_table = 'payments'
        verbose_name = _('دفعة')
        verbose_name_plural = _('الدفعات')
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['contract', 'payment_type']),
            models.Index(fields=['payer']),
            models.Index(fields=['payee']),
            models.Index(fields=['payment_number']),
            models.Index(fields=['due_date']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['created_at', 'updated_at']),
        ]

    def __str__(self):
        return f"{self.payment_number} - {self.amount} {self.currency}"

    def clean(self):
        if self.amount <= 0:
            raise ValidationError(_('يجب أن يكون مبلغ الدفع موجباً'))
        if self.pk:
            try:
                original = Payment.objects.get(pk=self.pk)
                if original.status != self.status:
                    self.validate_status_transition(
                        original.status,
                        self.status,
                        self.STATUS_TRANSITIONS
                    )
            except Payment.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        if self.status == 'completed' and self.confirmed_by and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.status == 'pending' and self.due_date:
            return self.due_date < timezone.now().date()
        return False

    @property
    def receipt_url(self):
        files = self.get_json_field('files')
        if not files:
            return None
        for file in files:
            if file.get('file_type') == 'receipt':
                return file.get('path')
        return files[0].get('path') if files else None

    def confirm_payment(self, user):
        self.status = 'completed'
        self.confirmed_by = user
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_by', 'confirmed_at', 'updated_at'])
        if self.payment_type == 'full_payment' and self.contract.status in ['pending_payment', 'signed']:
            self.contract.status = 'active'
            self.contract.save(update_fields=['status', 'updated_at'])
        return True

class Transaction(BaseModel, StatusTransitionMixin):
    """Transaction model for financial transactions between users"""
    TRANSACTION_TYPES = [
        ('deposit', _('عربون')),
        ('payment', _('دفعة')),
        ('refund', _('استرداد')),
        ('commission', _('عمولة')),
        ('fee', _('رسوم')),
        ('tax', _('ضريبة')),
        ('withdrawal', _('سحب')),
        ('transfer', _('تحويل')),
    ]

    TRANSACTION_STATUS = [
        ('pending', _('معلق')),
        ('processing', _('قيد المعالجة')),
        ('completed', _('مكتمل')),
        ('failed', _('فاشل')),
        ('cancelled', _('ملغى')),
        ('disputed', _('متنازع عليه')),
    ]

    STATUS_TRANSITIONS = {
        'pending': ['processing', 'completed', 'failed', 'cancelled'],
        'processing': ['completed', 'failed', 'cancelled'],
        'completed': ['disputed', 'refunded'],
        'failed': ['pending', 'cancelled'],
        'cancelled': [],
        'disputed': ['completed', 'failed', 'cancelled'],
    }

    transaction_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('رقم المعاملة')
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name=_('نوع المعاملة')
    )
    description = models.TextField(verbose_name=_('وصف المعاملة'))

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('المبلغ')
    )
    currency = models.CharField(
        max_length=3,
        default='SAR',
        verbose_name=_('العملة')
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=1.0,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('سعر الصرف')
    )
    fee_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('مبلغ الرسوم')
    )
    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('مبلغ الضريبة')
    )

    from_user = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='outgoing_transactions',
        verbose_name=_('من المستخدم')
    )
    to_user = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='incoming_transactions',
        verbose_name=_('إلى المستخدم')
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('الدفعة المرتبطة')
    )
    auction = models.ForeignKey(
        Auction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('المزاد المرتبط')
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('العقد المرتبط')
    )

    transaction_date = models.DateTimeField(verbose_name=_('تاريخ المعاملة'))
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default='pending',
        verbose_name=_('حالة المعاملة')
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('المرجع')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('ملاحظات')
    )

    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('تاريخ المعالجة')
    )
    processed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_transactions',
        verbose_name=_('تمت المعالجة بواسطة')
    )

    class Meta:
        db_table = 'transactions'
        verbose_name = _('معاملة مالية')
        verbose_name_plural = _('معاملات مالية')
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['from_user', 'to_user']),
            models.Index(fields=['transaction_number']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['payment']),
            models.Index(fields=['auction']),
            models.Index(fields=['contract']),
            models.Index(fields=['processed_by']),
            models.Index(fields=['created_at', 'updated_at']),
        ]

    def __str__(self):
        return f"{self.transaction_number} - {self.amount} {self.currency}"

    def clean(self):
        if self.amount <= 0:
            raise ValidationError(_('المبلغ يجب أن يكون موجبًا'))
        if self.pk:
            try:
                original = Transaction.objects.get(pk=self.pk)
                if original.status != self.status:
                    self.validate_status_transition(
                        original.status,
                        self.status,
                        self.STATUS_TRANSITIONS
                    )
            except Transaction.DoesNotExist:
                pass
        if not self.payment and not self.auction and not self.contract:
            raise ValidationError(_('يجب تحديد دفعة أو مزاد أو عقد مرتبط بالمعاملة'))

    def save(self, *args, **kwargs):
        if not self.transaction_date:
            self.transaction_date = timezone.now()
        if self.status == 'completed' and not self.processed_at and self.processed_by:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        return self.amount + self.fee_amount + self.tax_amount

    @property
    def is_income(self):
        return self.transaction_type in ['deposit', 'payment', 'commission', 'fee']

    @property
    def is_expense(self):
        return self.transaction_type in ['refund', 'withdrawal']

    def mark_as_completed(self, processor=None):
        if self.status not in ['pending', 'processing']:
            raise ValidationError(_('لا يمكن إكمال معاملة بحالة {self.status}'))
        self.status = 'completed'
        if processor:
            self.processed_by = processor
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_by', 'processed_at', 'updated_at'])
        return True

    def mark_as_failed(self, reason=None):
        if self.status not in ['pending', 'processing']:
            raise ValidationError(_('لا يمكن تحديد معاملة بحالة {self.status} كفاشلة'))
        self.status = 'failed'
        if reason:
            self.notes = reason
        self.save(update_fields=['status', 'notes', 'updated_at'])
        return True

class PropertyView(BaseModel, JsonFieldMixin):
    """Model for detailed property view information"""
    VIEW_TYPE_CHOICES = (
        ('OCEAN', _('إطلالة على المحيط')),
        ('MOUNTAIN', _('إطلالة على الجبل')),
        ('CITY', _('إطلالة على المدينة')),
        ('FOREST', _('إطلالة على الغابة')),
        ('LAKE', _('إطلالة على البحيرة')),
        ('CUSTOM', _('إطلالة مخصصة')),
    )

    auction = models.OneToOneField(
        Auction,
        on_delete=models.CASCADE,
        related_name='property_view',
        verbose_name=_('المزاد')
    )
    view_type = models.CharField(
        max_length=20,
        choices=VIEW_TYPE_CHOICES,
        verbose_name=_('نوع الإطلالة')
    )
    size_sqm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('المساحة (متر مربع)')
    )
    location = models.CharField(
        max_length=255,
        verbose_name=_('الموقع')
    )
    address = models.TextField(
        verbose_name=_('العنوان')
    )
    elevation = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('الارتفاع')
    )
    view_direction = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('اتجاه الإطلالة')
    )
    legal_description = models.TextField(
        verbose_name=_('الوصف القانوني')
    )
    condition = models.TextField(
        verbose_name=_('الحالة')
    )
    historical_views = models.TextField(
        default='{}',
        blank=True,
        verbose_name=_('الإطلالات التاريخية')
    )
    images = models.TextField(
        default='[]',
        blank=True,
        verbose_name=_('الصور')
    )

    class Meta:
        verbose_name = _('عرض العقار')
        verbose_name_plural = _('عروض العقارات')
        indexes = [
            models.Index(fields=['view_type']),
            models.Index(fields=['location']),
            models.Index(fields=['auction']),
            models.Index(fields=['size_sqm']),
            models.Index(fields=['elevation']),
            models.Index(fields=['created_at', 'updated_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_view_type_display()} في {self.location}"

    def clean(self):
        if self.size_sqm <= 0:
            raise ValidationError(_('يجب أن تكون المساحة أكبر من الصفر'))
        property_from_auction = self.auction.related_property
        if property_from_auction.address != self.address and property_from_auction.city not in self.location:
            logger.warning(f"Property view address '{self.address}' doesn't match property address '{property_from_auction.address}'")

    def save(self, *args, **kwargs):
        if isinstance(self.historical_views, dict):
            self.historical_views = json.dumps(self.historical_views)
        if isinstance(self.images, list):
            self.images = json.dumps(self.images)
        super().save(*args, **kwargs)

    @property
    def main_image_url(self):
        images = self.get_json_field('images')
        if not images:
            return None
        return images[0].get('path') if images else None

    @property
    def formatted_elevation(self):
        if self.elevation is None:
            return None
        return f"{self.elevation} m"

    @property
    def related_property(self):
        return self.auction.related_property if self.auction else None

class MessageThread(models.Model, JsonFieldMixin):
    """
    Model representing a conversation thread between users.

    This model organizes messages related to properties, auctions, or contracts,
    tracking participants, status, and metadata.
    """
    # Choices for thread types
    THREAD_TYPES = [
        ('inquiry', _('استفسار')),
        ('support', _('دعم')),
        ('negotiation', _('تفاوض')),
        ('general', _('عام')),
        ('notification', _('إشعار')),
        ('system', _('نظام')),
    ]

    # Choices for thread status
    THREAD_STATUS = [
        ('active', _('نشط')),
        ('closed', _('مغلق')),
        ('archived', _('مؤرشف')),
        ('deleted', _('محذوف')),
    ]

    # Core fields
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_('المعرف العالمي'),
        help_text=_('Unique identifier for the thread.')
    )
    subject = models.CharField(
        max_length=255,
        verbose_name=_('الموضوع'),
        help_text=_('Subject of the conversation thread.')
    )
    slug = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name=_('الرابط المختصر'),
        help_text=_('URL-friendly identifier for the thread.')
    )
    thread_type = models.CharField(
        max_length=20,
        choices=THREAD_TYPES,
        default='general',
        verbose_name=_('نوع المحادثة'),
        help_text=_('Type of conversation (e.g., inquiry, support).')
    )
    status = models.CharField(
        max_length=20,
        choices=THREAD_STATUS,
        default='active',
        verbose_name=_('حالة المحادثة'),
        help_text=_('Current status of the thread.')
    )

    # Relationships to related entities
    related_property = models.ForeignKey(
        'Property',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_threads',
        verbose_name=_('العقار المرتبط'),
        help_text=_('Property associated with this thread, if any.')
    )
    related_auction = models.ForeignKey(
        'Auction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_threads',
        verbose_name=_('المزاد المرتبط'),
        help_text=_('Auction associated with this thread, if any.')
    )
    related_contract = models.ForeignKey(
        'Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_threads',
        verbose_name=_('العقد المرتبط'),
        help_text=_('Contract associated with this thread, if any.')
    )

    # Thread metadata
    creator = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_threads',
        verbose_name=_('منشئ المحادثة'),
        help_text=_('User who created the thread.')
    )
    is_private = models.BooleanField(
        default=False,
        verbose_name=_('محادثة خاصة'),
        help_text=_('Whether the thread is private.')
    )
    is_system_thread = models.BooleanField(
        default=False,
        verbose_name=_('محادثة نظام'),
        help_text=_('Whether the thread is system-generated.')
    )
    last_message_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('تاريخ آخر رسالة'),
        help_text=_('Timestamp of the most recent message.')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء'),
        help_text=_('When the thread was created.')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاريخ التحديث'),
        help_text=_('When the thread was last updated.')
    )

    class Meta:
        db_table = 'message_threads'
        verbose_name = _('محادثة')
        verbose_name_plural = _('المحادثات')
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['thread_type'], name='idx_thread_type'),
            models.Index(fields=['status'], name='idx_status'),
            models.Index(fields=['creator'], name='idx_creator'),
            models.Index(fields=['related_property'], name='idx_related_property'),
            models.Index(fields=['related_auction'], name='idx_related_auction'),
            models.Index(fields=['related_contract'], name='idx_related_contract'),
            models.Index(fields=['is_private'], name='idx_is_private'),
            models.Index(fields=['is_system_thread'], name='idx_is_system_thread'),
            models.Index(fields=['last_message_at'], name='idx_last_message_at'),
            models.Index(fields=['created_at', 'updated_at'], name='idx_timestamps'),
            models.Index(fields=['slug'], name='idx_slug'),
        ]

    def __str__(self):
        """String representation of the thread."""
        return f"{self.subject} ({self.get_thread_type_display()})"

    def generate_unique_slug(self):
        """
        Generate a unique slug based on subject, timestamp, and random suffix.

        Raises:
            ValueError: If a unique slug cannot be generated after max retries.
        """
        base_slug = arabic_slugify(self.subject) or str(self.uuid)[:8]
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        max_retries = 10
        attempt = 0

        while attempt < max_retries:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            unique_slug = f"{base_slug}-{timestamp}-{random_suffix}"
            if not MessageThread.objects.filter(slug=unique_slug).exists():
                return unique_slug
            attempt += 1
            logger.debug(f"Slug collision detected: {unique_slug}, attempt {attempt}")

        raise ValueError(f"Failed to generate unique slug for '{self.subject}' after {max_retries} attempts")

    def save(self, *args, **kwargs):
        """
        Save the thread instance, ensuring a slug is generated if not present.

        Args:
            *args: Positional arguments passed to the parent save method.
            **kwargs: Keyword arguments passed to the parent save method.
        """
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)
        logger.debug(f"Saved MessageThread with ID: {self.pk}, Slug: {self.slug}")

    @property
    def participants(self):
        """Get all active participants in this thread."""
        return CustomUser.objects.filter(
            thread_memberships__thread=self,
            thread_memberships__is_active=True
        )

    @property
    def unread_count(self):
        """Calculate the total unread messages across all participants."""
        return sum(
            participant.unread_count
            for participant in self.thread_participants.filter(is_active=True)
        )

    @property
    def message_count(self):
        """Count the total number of messages in the thread."""
        return self.messages.count()

    def add_participant(self, user, role='member'):
        """
        Add a user as a participant to the thread.

        Args:
            user (CustomUser): The user to add.
            role (str): The role to assign (default: 'member').

        Returns:
            ThreadParticipant: The created or updated participant instance.
        """
        participant, created = ThreadParticipant.objects.get_or_create(
            thread=self,
            user=user,
            defaults={'role': role, 'is_active': True}
        )
        if not created and not participant.is_active:
            participant.is_active = True
            participant.save(update_fields=['is_active', 'updated_at'])
            logger.debug(f"Reactivated participant {user} in thread {self.id}")
        elif created:
            logger.debug(f"Added new participant {user} to thread {self.id}")
        return participant

    def remove_participant(self, user):
        """
        Remove a participant from the thread by marking them as inactive.

        Args:
            user (CustomUser): The user to remove.

        Returns:
            bool: True if participant was removed, False if not found.
        """
        participant = ThreadParticipant.objects.filter(
            thread=self,
            user=user,
            is_active=True
        ).first()
        if participant:
            participant.is_active = False
            participant.save(update_fields=['is_active', 'updated_at'])
            logger.debug(f"Removed participant {user} from thread {self.id}")
            return True
        logger.debug(f"No active participant {user} found in thread {self.id}")
        return False

    def mark_as_read_for_user(self, user):
        """
        Mark all messages in the thread as read for a specific user.

        Args:
            user (CustomUser): The user for whom to mark messages as read.

        Returns:
            int: Number of messages marked as read.
        """
        participant = ThreadParticipant.objects.filter(
            thread=self,
            user=user,
            is_active=True
        ).first()
        if participant:
            count = participant.mark_all_as_read()
            logger.debug(f"Marked {count} messages as read for {user} in thread {self.id}")
            return count
        logger.debug(f"User {user} is not an active participant in thread {self.id}")
        return 0

    def close_thread(self):
        """
        Close the thread if it’s not already closed.

        Returns:
            bool: True if closed, False if already closed.
        """
        if self.status != 'closed':
            self.status = 'closed'
            self.save(update_fields=['status', 'updated_at'])
            logger.debug(f"Closed thread {self.id}")
            return True
        logger.debug(f"Thread {self.id} is already closed")
        return False

    def reopen_thread(self):
        """
        Reopen the thread if it’s not already active.

        Returns:
            bool: True if reopened, False if already active.
        """
        if self.status != 'active':
            self.status = 'active'
            self.save(update_fields=['status', 'updated_at'])
            logger.debug(f"Reopened thread {self.id}")
            return True
        logger.debug(f"Thread {self.id} is already active")
        return False


class Message(BaseModel, JsonFieldMixin):
    """Model for communication between users"""
    MESSAGE_TYPES = [
        ('inquiry', _('استفسار')),
        ('offer', _('عرض')),
        ('negotiation', _('تفاوض')),
        ('notification', _('إشعار')),
        ('update', _('تحديث')),
        ('support', _('دعم')),
        ('reply', _('رد')),
    ]

    MESSAGE_STATUS = [
        ('sent', _('مرسلة')),
        ('delivered', _('تم التسليم')),
        ('read', _('مقروءة')),
        ('replied', _('تم الرد')),
        ('archived', _('مؤرشفة')),
    ]

    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('المحادثة')
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('المرسل')
    )
    subject = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('الموضوع'))
    content = models.TextField(verbose_name=_('المحتوى'))
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='inquiry',
        verbose_name=_('نوع الرسالة')
    )
    status = models.CharField(
        max_length=20,
        choices=MESSAGE_STATUS,
        default='sent',
        verbose_name=_('حالة الرسالة')
    )

    sent_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإرسال'))
    delivered_at = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ التسليم'))
    read_at = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ القراءة'))

    related_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name=_('العقار المرتبط')
    )
    related_auction = models.ForeignKey(
        Auction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name=_('المزاد المرتبط')
    )
    related_contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name=_('العقد المرتبط')
    )

    parent_message = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('الرسالة الأصلية')
    )

    attachments = models.TextField(default='[]', blank=True, null=True, verbose_name=_('المرفقات'))

    is_system_message = models.BooleanField(default=False, verbose_name=_('رسالة نظام'))
    is_important = models.BooleanField(default=False, verbose_name=_('هامة'))

    class Meta:
        db_table = 'messages'
        verbose_name = _('رسالة')
        verbose_name_plural = _('الرسائل')
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['thread', 'sent_at']),
            models.Index(fields=['sender', 'status']),
            models.Index(fields=['is_system_message']),
            models.Index(fields=['message_type']),
            models.Index(fields=['related_property']),
            models.Index(fields=['related_auction']),
            models.Index(fields=['related_contract']),
            models.Index(fields=['parent_message']),
            models.Index(fields=['is_important']),
            models.Index(fields=['delivered_at']),
            models.Index(fields=['read_at']),
            models.Index(fields=['created_at', 'updated_at']),
        ]

    def __str__(self):
        return f"{self.subject or 'رسالة'} من {self.sender}"

    def clean(self):
        if not ThreadParticipant.objects.filter(thread=self.thread, user=self.sender, is_active=True).exists():
            raise ValidationError(_('المرسل يجب أن يكون مشاركًا نشطًا في المحادثة'))
        if not self.related_property and self.thread.related_property:
            self.related_property = self.thread.related_property
        if not self.related_auction and self.thread.related_auction:
            self.related_auction = self.thread.related_auction
        if not self.related_contract and self.thread.related_contract:
            self.related_contract = self.thread.related_contract

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if isinstance(self.attachments, list):
            self.attachments = json.dumps(self.attachments)
        if is_new:
            if not self.related_property and self.thread.related_property:
                self.related_property = self.thread.related_property
            if not self.related_auction and self.thread.related_auction:
                self.related_auction = self.thread.related_auction
            if not self.related_contract and self.thread.related_contract:
                self.related_contract = self.thread.related_contract
            if self.parent_message:
                self.parent_message.status = 'replied'
                self.parent_message.save(update_fields=['status', 'updated_at'])
        super().save(*args, **kwargs)
        if is_new:
            self.thread.last_message_at = self.sent_at
            self.thread.save(update_fields=['last_message_at', 'updated_at'])
            if self.parent_message:
                self.parent_message.mark_as_read()

    @property
    def has_attachments(self):
        attachments = self.get_json_field('attachments')
        return bool(attachments)

    @property
    def is_read(self):
        return self.status in ['read', 'replied']

    def mark_as_delivered(self):
        if not self.delivered_at:
            self.status = 'delivered'
            self.delivered_at = timezone.now()
            self.save(update_fields=['status', 'delivered_at', 'updated_at'])
        return True

    def mark_as_read(self, reader=None):
        if self.status not in ['read', 'replied']:
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at', 'updated_at'])
            if reader:
                participant = ThreadParticipant.objects.filter(thread=self.thread, user=reader).first()
                if participant:
                    participant.last_read_at = timezone.now()
                    participant.save(update_fields=['last_read_at', 'updated_at'])
        return True

class ThreadParticipant(BaseModel):
    """Model for tracking user participation in message threads"""
    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='thread_participants',
        verbose_name=_('المحادثة')
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='thread_memberships',
        verbose_name=_('المستخدم')
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        related_name='thread_participations',
        verbose_name=_('الدور في المحادثة')
    )

    custom_permissions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('صلاحيات مخصصة'),
        help_text=_('صلاحيات خاصة بهذه المحادثة فقط')
    )

    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))
    is_muted = models.BooleanField(default=False, verbose_name=_('صامت'))
    last_read_at = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ آخر قراءة'))

    class Meta:
        db_table = 'thread_participants'
        verbose_name = _('مشارك في محادثة')
        verbose_name_plural = _('مشاركون في محادثة')
        unique_together = ['thread', 'user']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['thread', 'role']),
            models.Index(fields=['is_muted']),
            models.Index(fields=['last_read_at']),
            models.Index(fields=['created_at', 'updated_at']),
        ]

    def __str__(self):
        role_name = self.role.get_name_display() if self.role else _('بدون دور')
        return f"{self.user} في محادثة {self.thread.subject} ({role_name})"

    @property
    def has_unread_messages(self):
        if not self.last_read_at:
            return self.thread.messages.exclude(sender=self.user).exists()
        return self.thread.messages.filter(
            sent_at__gt=self.last_read_at
        ).exclude(sender=self.user).exists()

    @property
    def unread_count(self):
        if not self.last_read_at:
            return self.thread.messages.exclude(sender=self.user).count()
        return self.thread.messages.filter(
            sent_at__gt=self.last_read_at
        ).exclude(sender=self.user).count()

    def mark_all_as_read(self):
        if not self.is_active:
            return 0
        now = timezone.now()
        if not self.last_read_at:
            unread_messages = self.thread.messages.exclude(sender=self.user)
        else:
            unread_messages = self.thread.messages.filter(
                sent_at__gt=self.last_read_at
            ).exclude(sender=self.user)
        count = unread_messages.update(
            status='read',
            read_at=now
        )
        self.last_read_at = now
        self.save(update_fields=['last_read_at', 'updated_at'])
        return count

    def leave_thread(self):
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
        return True

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        self.save(update_fields=['is_muted', 'updated_at'])
        return self.is_muted

    def has_permission(self, permission_name):
        if permission_name in self.custom_permissions:
            return self.custom_permissions.get(permission_name, False)
        if self.role and hasattr(self.role, 'default_permissions'):
            return self.role.default_permissions.get(permission_name, False)
        return self.user.has_auction_permission(permission_name)

    def assign_role(self, role_name):
        try:
            role = Role.objects.get(name=role_name)
            self.role = role
            self.save(update_fields=['role', 'updated_at'])
            return True
        except Role.DoesNotExist:
            return False

    def set_custom_permission(self, permission_name, value=True):
        if not self.custom_permissions:
            self.custom_permissions = {}
        self.custom_permissions[permission_name] = value
        self.save(update_fields=['custom_permissions', 'updated_at'])
        return self.custom_permissions

class Notification(BaseModel):
    """Model for system notifications"""
    NOTIFICATION_TYPES = [
        ('auction_start', _('بدء مزاد')),
        ('auction_end', _('انتهاء مزاد')),
        ('new_bid', _('عطاء جديد')),
        ('outbid', _('تم تجاوز العطاء')),
        ('winning_bid', _('عطاء فائز')),
        ('auction_status', _('تغيير حالة المزاد')),
        ('property_listed', _('إدراج عقار جديد')),
        ('property_status', _('تغيير حالة العقار')),
        ('payment', _('دفعة جديدة')),
        ('contract_status', _('تغيير حالة العقد')),
        ('message', _('رسالة جديدة')),
        ('system', _('إشعار نظام')),
    ]

    CHANNELS = [
        ('app', _('تطبيق')),
        ('email', _('بريد إلكتروني')),
        ('sms', _('رسالة نصية')),
        ('push', _('إشعار فوري')),
    ]

    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('المستلم')
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        verbose_name=_('نوع الإشعار')
    )
    title = models.CharField(max_length=255, verbose_name=_('العنوان'))
    content = models.TextField(verbose_name=_('المحتوى'))
    channel = models.CharField(
        max_length=20,
        choices=CHANNELS,
        default='app',
        verbose_name=_('قناة الإشعار')
    )

    related_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('العقار المرتبط')
    )
    related_auction = models.ForeignKey(
        Auction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('المزاد المرتبط')
    )
    related_bid = models.ForeignKey(
        Bid,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('العطاء المرتبط')
    )
    related_contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('العقد المرتبط')
    )
    related_payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('الدفعة المرتبطة')
    )
    related_message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('الرسالة المرتبطة')
    )

    is_read = models.BooleanField(default=False, verbose_name=_('تمت القراءة'))
    read_at = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ القراءة'))
    is_sent = models.BooleanField(default=False, verbose_name=_('تم الإرسال'))
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name=_('تاريخ الإرسال'))

    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('الأيقونة'))
    color = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('اللون'))
    action_url = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('رابط العمل'))

    class Meta:
        db_table = 'notifications'
        verbose_name = _('إشعار')
        verbose_name_plural = _('إشعارات')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['channel']),
            models.Index(fields=['is_sent']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['read_at']),
            models.Index(fields=['related_property']),
            models.Index(fields=['related_auction']),
            models.Index(fields=['related_bid']),
            models.Index(fields=['related_contract']),
            models.Index(fields=['related_payment']),
            models.Index(fields=['related_message']),
            models.Index(fields=['created_at', 'updated_at']),
        ]

    def __str__(self):
        return f"{self.title} لـ {self.recipient}"

    def clean(self):
        if self.notification_type == 'auction_start' and not self.related_auction:
            raise ValidationError(_('إشعار بدء مزاد يتطلب تحديد المزاد المرتبط'))
        if self.notification_type == 'auction_end' and not self.related_auction:
            raise ValidationError(_('إشعار انتهاء مزاد يتطلب تحديد المزاد المرتبط'))
        if self.notification_type == 'new_bid' and not self.related_bid:
            raise ValidationError(_('إشعار عطاء جديد يتطلب تحديد العطاء المرتبط'))
        if self.notification_type == 'payment' and not self.related_payment:
            raise ValidationError(_('إشعار دفعة جديدة يتطلب تحديد الدفعة المرتبطة'))
        if self.notification_type == 'message' and not self.related_message:
            raise ValidationError(_('إشعار رسالة جديدة يتطلب تحديد الرسالة المرتبطة'))

    def save(self, *args, **kwargs):
        if self.is_sent and not self.sent_at:
            self.sent_at = timezone.now()
        super().save(*args, **kwargs)

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
        return True

    def mark_as_sent(self):
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save(update_fields=['is_sent', 'sent_at', 'updated_at'])
        return True

    @property
    def is_actionable(self):
        return bool(self.action_url)

    @classmethod
    def create_bid_notification(cls, bid, recipient=None):
        auction = bid.auction
        property = auction.related_property
        if not recipient:
            if bid.bidder == auction.created_by and property.owner != auction.created_by:
                recipient = property.owner
            else:
                recipient = auction.created_by
        notification = cls.objects.create(
            recipient=recipient,
            notification_type='new_bid',
            title=_('مزايدة جديدة'),
            content=_('تم تسجيل مزايدة جديدة بقيمة {} على {}').format(
                bid.bid_amount, auction.title
            ),
            related_auction=auction,
            related_property=property,
            related_bid=bid,
            icon='money',
            color='primary',
            action_url=f'/auctions/{auction.id}'
        )
        return notification
