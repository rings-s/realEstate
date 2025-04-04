# Path: accounts/models.py
# This file defines the user and role models for the auction platform
# The CustomUser model includes a UUID field to support more robust identification

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.db import transaction
import random
import uuid
from django.core.validators import RegexValidator, MinValueValidator

class Role(models.Model):
    """
    Defines real estate auction platform user roles and associated permissions
    """
    ADMIN = 'admin'
    SELLER = 'seller'
    BUYER = 'buyer'
    INSPECTOR = 'inspector'
    LEGAL = 'legal'
    AGENT = 'agent'
    APPRAISER = 'appraiser'

    ROLE_CHOICES = [
        (ADMIN, _('المشرف')),
        (SELLER, _('بائع العقارات')),
        (BUYER, _('مشتري العقارات')),
        (INSPECTOR, _('مفتش العقارات')),
        (LEGAL, _('ممثل قانوني')),
        (AGENT, _('وكيل عقارات')),
        (APPRAISER, _('مثمن')),
    ]

    name = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        unique=True,
        verbose_name=_('الاسم'),
        help_text=_('اسم الدور يحدد صلاحيات المستخدم ومستويات الوصول')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('الوصف'),
        help_text=_('وصف تفصيلي لمسؤوليات الدور')
    )
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('الصلاحيات'),
        blank=True,
        help_text=_('الصلاحيات المحددة الممنوحة لهذا الدور'),
        related_name='auction_roles'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        verbose_name = _('دور')
        verbose_name_plural = _('الأدوار')
        app_label = 'accounts'  # Explicitly set the app_label

    def __str__(self):
        return self.get_name_display()

    @property
    def default_permissions(self):
        """
        Define default permissions for each real estate auction platform role
        """
        permissions_map = {
            self.ADMIN: {
                'can_manage_users': True,
                'can_manage_roles': True,
                'can_manage_auctions': True,
                'can_manage_contracts': True,
                'can_view_analytics': True,
                'can_manage_system': True,
            },
            self.SELLER: {
                'can_create_auctions': True,
                'can_manage_own_auctions': True,
                'can_view_own_analytics': True,
                'can_manage_own_contracts': True,
                'can_interact_with_buyers': True,
                'can_upload_property_documents': True,
            },
            self.BUYER: {
                'can_view_auctions': True,
                'can_place_bids': True,
                'can_manage_own_contracts': True,
                'can_view_own_history': True,
                'can_interact_with_sellers': True,
                'can_request_property_viewings': True,
            },
            self.INSPECTOR: {
                'can_inspect_properties': True,
                'can_create_inspection_reports': True,
                'can_verify_documents': True,
                'can_update_property_status': True,
            },
            self.LEGAL: {
                'can_review_contracts': True,
                'can_manage_legal_documents': True,
                'can_verify_compliance': True,
                'can_handle_disputes': True,
                'can_verify_property_titles': True,
            },
            self.AGENT: {
                'can_create_auctions': True,
                'can_manage_client_auctions': True,
                'can_view_client_analytics': True,
                'can_interact_with_buyers': True,
                'can_represent_sellers': True,
                'can_arrange_property_viewings': True,
            }
        }
        return permissions_map.get(self.name, {})


class CustomUserManager(BaseUserManager):
    """
    Custom user manager that handles email as the unique identifier
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('البريد الإلكتروني مطلوب'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('يجب أن يكون المستخدم الخارق لديه is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('يجب أن يكون المستخدم الخارق لديه is_superuser=True.'))

        user = self.create_user(email, password, **extra_fields)

        # Add admin role to superuser
        admin_role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        user.roles.add(admin_role)

        return user


class CustomUser(AbstractUser):
    """
    Custom user model with email as the unique identifier
    and multi-role capabilities for real estate platform

    Note: This model has both an integer primary key (id) and a UUID field
    to support compatibility with existing relationships while allowing
    UUID-based lookups
    """
    # Add a UUID field alongside the existing primary key
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_('UUID'))

    username = None  # Remove username field
    email = models.EmailField(_('البريد الإلكتروني'), unique=True)
    first_name = models.CharField(_('الاسم الأول'), max_length=30)
    last_name = models.CharField(_('اسم العائلة'), max_length=30)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("يجب إدخال رقم الهاتف بالصيغة: '+999999999'. يسمح بحد أقصى 15 رقم.")
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, verbose_name=_('رقم الهاتف'))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_('تاريخ الميلاد'))
    is_verified = models.BooleanField(default=False, verbose_name=_('تم التحقق'))
    verification_code = models.CharField(max_length=6, blank=True, verbose_name=_('رمز التحقق'))
    verification_code_created = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ إنشاء رمز التحقق'))
    reset_code = models.CharField(max_length=6, blank=True, verbose_name=_('رمز إعادة تعيين كلمة المرور'))
    reset_code_created = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ إنشاء رمز إعادة التعيين'))
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name=_('الصورة الشخصية'))
    roles = models.ManyToManyField(
        Role,
        verbose_name=_('الأدوار'),
        blank=True,
        help_text=_('الأدوار المخصصة لهذا المستخدم'),
        related_name='users'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')
        app_label = 'accounts'  # Explicitly set the app_label

    def __str__(self):
        return self.email

    def has_role(self, role_name):
        """Check if user has a specific role"""
        return self.roles.filter(name=role_name).exists()

    @property
    def role_names(self):
        """Get all of the user's role names"""
        return list(self.roles.values_list('name', flat=True))

    @property
    def primary_role(self):
        """
        Get the user's primary role using a priority system:
        Admin > Agent > Inspector > Legal > Seller > Buyer
        """
        # Role priority order (highest to lowest)
        role_priority = [Role.ADMIN, Role.AGENT, Role.INSPECTOR, Role.LEGAL, Role.SELLER, Role.BUYER]

        # Check for each role in order of priority
        for role_name in role_priority:
            if self.has_role(role_name):
                return role_name

        return None

    def has_auction_permission(self, permission_name):
        """
        Check if user has specific auction-related permission
        by checking all assigned roles
        """
        # Check each role the user has
        for role in self.roles.all():
            if role.default_permissions.get(permission_name, False):
                return True
        return False

    def add_role(self, role_name):
        """Add a role to the user by name"""
        if role_name not in [choice[0] for choice in Role.ROLE_CHOICES]:
            raise ValueError(f"Invalid role name: {role_name}")

        role, created = Role.objects.get_or_create(name=role_name)
        self.roles.add(role)

    def remove_role(self, role_name):
        """Remove a role from the user by name"""
        try:
            role = Role.objects.get(name=role_name)
            self.roles.remove(role)
        except Role.DoesNotExist:
            pass  # Role doesn't exist, nothing to remove

    def generate_verification_code(self):
        """Generate a random 6-digit verification code"""
        code = str(random.randint(100000, 999999))
        self.verification_code = code
        self.verification_code_created = timezone.now()
        self.save(update_fields=['verification_code', 'verification_code_created'])
        return code

    def generate_reset_code(self):
        """Generate a random 6-digit password reset code"""
        code = str(random.randint(100000, 999999))
        self.reset_code = code
        self.reset_code_created = timezone.now()
        self.save(update_fields=['reset_code', 'reset_code_created'])
        return code

    def verify_account(self, code):
        """Verify user account with the provided code"""
        # Check if code is valid and not expired (valid for 24 hours)
        if (self.verification_code and
            self.verification_code == code and
            self.verification_code_created and
            timezone.now() < self.verification_code_created + timezone.timedelta(hours=24)):

            self.is_verified = True
            self.verification_code = ''
            self.save(update_fields=['is_verified', 'verification_code'])
            return True
        return False

    def reset_password(self, code, new_password):
        """Reset user password with the provided code"""
        # Check if code is valid and not expired (valid for 1 hour)
        if (self.reset_code and
            self.reset_code == code and
            self.reset_code_created and
            timezone.now() < self.reset_code_created + timezone.timedelta(hours=1)):

            self.set_password(new_password)
            self.reset_code = ''
            self.save(update_fields=['password', 'reset_code'])
            return True
        return False

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Override save to create user profile if it doesn't exist"""
        creating = self._state.adding
        super().save(*args, **kwargs)

        if creating:
            UserProfile.objects.get_or_create(user=self)


class UserProfile(models.Model):
    """
    Extended user profile for additional information specific to real estate platform
    """
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='profile', verbose_name=_('المستخدم'))
    bio = models.TextField(blank=True, verbose_name=_('نبذة شخصية'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))
    company_name = models.CharField(max_length=200, blank=True, verbose_name=_('اسم الشركة'))
    company_registration = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        null=True,
        verbose_name=_('رقم تسجيل الشركة')
    )
    tax_id = models.CharField(max_length=50, blank=True, verbose_name=_('الرقم الضريبي'))
    address = models.TextField(blank=True, verbose_name=_('العنوان'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('المدينة'))
    state = models.CharField(max_length=100, blank=True, verbose_name=_('المحافظة/الولاية'))
    postal_code = models.CharField(max_length=20, blank=True, verbose_name=_('الرمز البريدي'))
    country = models.CharField(max_length=100, blank=True, verbose_name=_('الدولة'))
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('الحد الائتماني')
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('التقييم')
    )
    license_number = models.CharField(max_length=50, blank=True,
                                     verbose_name=_('رقم الترخيص'),
                                     help_text=_("رقم ترخيص مزاولة المهنة للوكلاء العقاريين"))
    license_expiry = models.DateField(null=True, blank=True, verbose_name=_('تاريخ انتهاء الترخيص'))
    preferred_locations = models.TextField(blank=True,
                                          verbose_name=_('المواقع المفضلة'),
                                          help_text=_("قائمة المواقع المفضلة مفصولة بفواصل"))
    property_preferences = models.TextField(blank=True,
                                          verbose_name=_('تفضيلات العقارات'),
                                          help_text=_("تفضيلات نوع العقار للمشترين"))

    class Meta:
        verbose_name = _('ملف تعريف المستخدم')
        verbose_name_plural = _('ملفات تعريف المستخدمين')
        app_label = 'accounts'  # Explicitly set the app_label
