import os
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission
from django.utils.translation import gettext_lazy as _
# from django.utils import timezone # Duplicate import
from django.conf import settings
from django.db import transaction
import random
import uuid
from django.core.validators import RegexValidator, MinValueValidator

# --- Path Functions ---
# Corrected to use the instance directly (assuming instance is CustomUser)
# Using UUID for folder name for better uniqueness and obscurity than integer ID
def user_avatar_path(instance, filename):
    """ File will be uploaded to MEDIA_ROOT/users/<user_uuid>/avatars/<timestamp>_<filename> """
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    # Ensure instance has a uuid before accessing it (might not during initial creation before save)
    user_uuid = instance.uuid if instance.uuid else 'temp'
    return f'users/{user_uuid}/avatars/{timestamp}_{filename}'

# Corrected similarly for consistency (assuming instance is CustomUser or related model)
# If used for UserProfile, it should be instance.user.uuid
def user_document_path(instance, filename):
    """ For any other user-related documents """
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    # Adjust based on the model using this function
    # If used on UserProfile: user_uuid = instance.user.uuid if instance.user.uuid else 'temp'
    # If used on CustomUser: user_uuid = instance.uuid if instance.uuid else 'temp'
    user_uuid = getattr(getattr(instance, 'user', instance), 'uuid', 'temp') # More robust check
    return f'users/{user_uuid}/documents/{timestamp}_{filename}'

# --- Role Model ---
class Role(models.Model):
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
        help_text=_('الصلاحيات المحددة الممنوحة لهذا الدور (Django Permissions)'), # Clarified help text
        related_name='auction_roles'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        verbose_name = _('دور')
        verbose_name_plural = _('الأدوار')
        app_label = 'accounts'

    def __str__(self):
        return self.get_name_display()

    @property
    def default_permissions(self):
        """
        Defines default CUSTOM permissions/capabilities for each role.
        NOTE: These are string-based flags used by custom logic (e.g., has_auction_permission),
        they do NOT automatically grant Django Model Permissions stored in the 'permissions' field.
        """
        permissions_map = {
             self.ADMIN: {
                 'can_manage_users': True, 'can_manage_roles': True, 'can_manage_auctions': True,
                 'can_manage_contracts': True, 'can_view_analytics': True, 'can_manage_system': True,
             },
             self.SELLER: {
                 'can_create_auctions': True, 'can_manage_own_auctions': True, 'can_view_own_analytics': True,
                 'can_manage_own_contracts': True, 'can_interact_with_buyers': True, 'can_upload_property_documents': True,
             },
             self.BUYER: {
                 'can_view_auctions': True, 'can_place_bids': True, 'can_manage_own_contracts': True,
                 'can_view_own_history': True, 'can_interact_with_sellers': True, 'can_request_property_viewings': True,
             },
             self.INSPECTOR: {
                 'can_inspect_properties': True, 'can_create_inspection_reports': True, 'can_verify_documents': True,
                 'can_update_property_status': True,
             },
             self.LEGAL: {
                 'can_review_contracts': True, 'can_manage_legal_documents': True, 'can_verify_compliance': True,
                 'can_handle_disputes': True, 'can_verify_property_titles': True,
             },
             self.AGENT: {
                 'can_create_auctions': True, 'can_manage_client_auctions': True, 'can_view_client_analytics': True,
                 'can_interact_with_buyers': True, 'can_represent_sellers': True, 'can_arrange_property_viewings': True,
             },
             # APPRAISER role defined but no default permissions listed? Add if needed.
             # self.APPRAISER: { ... }
        }
        return permissions_map.get(self.name, {})

# --- Custom User Manager ---
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('البريد الإلكتروني مطلوب'))
        email = self.normalize_email(email)
        # Ensure default fields are handled if not provided
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True) # Consider setting to False until verified

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True) # Superusers should be verified

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('يجب أن يكون المستخدم الخارق لديه is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('يجب أن يكون المستخدم الخارق لديه is_superuser=True.'))

        # Use transaction.atomic for superuser creation including role assignment
        with transaction.atomic():
            user = self.create_user(email, password, **extra_fields)
            # Add admin role to superuser
            admin_role, created = Role.objects.get_or_create(name=Role.ADMIN)
            # If role was just created, consider adding default Django permissions to it here
            # based on your application's needs.
            user.roles.add(admin_role)
            # UserProfile should be created automatically by the overridden save method

        return user

# --- Custom User Model ---
class CustomUser(AbstractUser):
    # Add a UUID field alongside the existing primary key
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_('UUID'), db_index=True) # Added db_index

    username = None # Remove username field
    email = models.EmailField(_('البريد الإلكتروني'), unique=True, db_index=True) # Added db_index
    first_name = models.CharField(_('الاسم الأول'), max_length=150) # Increased length to match AbstractUser default
    last_name = models.CharField(_('اسم العائلة'), max_length=150) # Increased length to match AbstractUser default

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("يجب إدخال رقم الهاتف بالصيغة: '+999999999'. يسمح بحد أقصى 15 رقم.")
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, verbose_name=_('رقم الهاتف'))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_('تاريخ الميلاد'))
    is_verified = models.BooleanField(default=False, verbose_name=_('تم التحقق'), help_text=_('يشير إلى ما إذا كان المستخدم قد تحقق من بريده الإلكتروني.'))
    verification_code = models.CharField(max_length=6, blank=True, null=True, verbose_name=_('رمز التحقق')) # Allow null
    verification_code_created = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ إنشاء رمز التحقق'))
    reset_code = models.CharField(max_length=6, blank=True, null=True, verbose_name=_('رمز إعادة تعيين كلمة المرور')) # Allow null
    reset_code_created = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ إنشاء رمز إعادة التعيين'))

    # FIX: Use the corrected user_avatar_path function
    avatar = models.ImageField(upload_to=user_avatar_path, null=True, blank=True, verbose_name=_('الصورة الشخصية'))

    roles = models.ManyToManyField(
        Role,
        verbose_name=_('الأدوار'),
        blank=True,
        help_text=_('الأدوار المخصصة لهذا المستخدم'),
        related_name='users'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Ensure these match AbstractUser or are handled

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')
        app_label = 'accounts'

    def __str__(self):
        return self.email

    def has_role(self, role_name):
        """Check if user has a specific role by name"""
        return self.roles.filter(name=role_name).exists()

    @property
    def role_names(self):
        """Get a list of the user's role names"""
        # Use select_related or prefetch_related in views where this is accessed frequently
        return list(self.roles.values_list('name', flat=True))

    @property
    def primary_role(self):
        """
        Get the user's primary role using a defined priority system.
        Returns None if the user has no roles matching the priority list.
        """
        # Role priority order (highest to lowest)
        role_priority = [Role.ADMIN, Role.AGENT, Role.INSPECTOR, Role.LEGAL, Role.SELLER, Role.BUYER, Role.APPRAISER] # Added Appraiser

        # More efficient check if roles are prefetched
        current_roles = set(self.role_names) # Use set for faster lookups
        for role_name in role_priority:
            if role_name in current_roles:
                return role_name
        return None # Return None if no priority roles are found

    def has_auction_permission(self, permission_name):
        """
        Check if user has a specific custom auction-related permission flag
        by checking the 'default_permissions' dictionary of all assigned roles.
        """
        # Use prefetch_related('roles') in views for efficiency
        for role in self.roles.all():
            if role.default_permissions.get(permission_name, False):
                return True
        return False

    def add_role(self, role_name):
        """Add a role to the user by name. Returns True if added, False otherwise."""
        if role_name not in [choice[0] for choice in Role.ROLE_CHOICES]:
            # Consider logging this error or raising a specific exception
            # logger.warning(f"Attempted to add invalid role '{role_name}' to user {self.email}")
            # raise ValueError(f"Invalid role name: {role_name}")
             return False # Or raise error

        role, created = Role.objects.get_or_create(name=role_name)
        # Add returns True if the relation was created, False if it already existed
        _, added = self.roles.add(role) # Use the result of add()
        return added


    def remove_role(self, role_name):
        """Remove a role from the user by name. Returns True if removed, False otherwise."""
        try:
            role = self.roles.get(name=role_name) # Query through the user's roles
            self.roles.remove(role)
            return True
        except Role.DoesNotExist:
            return False # Role wasn't assigned or doesn't exist

    def generate_verification_code(self, length=6):
        """Generate a random verification code of specified length"""
        if length < 4: length = 4 # Ensure minimum length
        code = str(random.randint(int('1' + '0'*(length-1)), int('9'*length)))
        self.verification_code = code
        self.verification_code_created = timezone.now()
        # Only save relevant fields for efficiency
        self.save(update_fields=['verification_code', 'verification_code_created', 'is_verified']) # Ensure is_verified is False if regenerating
        return code

    def generate_reset_code(self, length=6):
        """Generate a random password reset code of specified length"""
        if length < 4: length = 4
        code = str(random.randint(int('1' + '0'*(length-1)), int('9'*length)))
        self.reset_code = code
        self.reset_code_created = timezone.now()
        self.save(update_fields=['reset_code', 'reset_code_created'])
        return code

    def verify_account(self, code):
        """Verify user account with the provided code. Clears the code on success."""
        if not self.verification_code or not self.verification_code_created:
            return False # No code to verify against

        # Check code match
        if self.verification_code != code:
            return False

        # Check expiry (e.g., 24 hours)
        expiry_time = self.verification_code_created + timezone.timedelta(hours=24)
        if timezone.now() > expiry_time:
             # Optionally clear expired code
             # self.verification_code = None
             # self.verification_code_created = None
             # self.save(update_fields=['verification_code', 'verification_code_created'])
            return False # Code expired

        # Verification successful
        self.is_verified = True
        self.verification_code = None # Clear code after use
        self.verification_code_created = None
        self.save(update_fields=['is_verified', 'verification_code', 'verification_code_created'])
        return True

    def reset_password(self, code, new_password):
        """Reset user password with the provided code. Clears the code on success."""
        if not self.reset_code or not self.reset_code_created:
            return False

        if self.reset_code != code:
            return False

        # Check expiry (e.g., 1 hour)
        expiry_time = self.reset_code_created + timezone.timedelta(hours=1)
        if timezone.now() > expiry_time:
            # Optionally clear expired code
            # self.reset_code = None
            # self.reset_code_created = None
            # self.save(update_fields=['reset_code', 'reset_code_created'])
            return False # Code expired

        # Reset successful
        self.set_password(new_password)
        self.reset_code = None # Clear code after use
        self.reset_code_created = None
        # Use update_fields to avoid potential side effects of full save()
        self.save(update_fields=['password', 'reset_code', 'reset_code_created'])
        return True

    # Overridden save method to ensure UserProfile creation
    @transaction.atomic # Ensure user and profile creation is atomic
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        # Generate UUID if it's not set (should be handled by default=uuid.uuid4)
        if not self.uuid:
             self.uuid = uuid.uuid4()
        super().save(*args, **kwargs) # Call the "real" save() method.

        # Create UserProfile only if the user is being created
        if is_new:
             # Use update_or_create for robustness, though get_or_create is usually sufficient here
             UserProfile.objects.update_or_create(user=self, defaults={})


# --- User Profile Model ---
class UserProfile(models.Model):
    # Use settings.AUTH_USER_MODEL for flexibility
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile', verbose_name=_('المستخدم'), primary_key=True) # Added primary_key=True for OneToOneField
    bio = models.TextField(blank=True, verbose_name=_('نبذة شخصية'))
    # Removed created_at/updated_at, often redundant if CustomUser tracks this
    # created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    # updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))
    company_name = models.CharField(max_length=200, blank=True, verbose_name=_('اسم الشركة'))
    company_registration = models.CharField(
        max_length=100,
        blank=True,
        unique=True, # Be cautious with unique=True on blank=True fields
        null=True,   # Allow null in DB to properly handle uniqueness on empty strings
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
        validators=[MinValueValidator(0)], # Rating typically >= 0, maybe MaxValueValidator(5)?
        verbose_name=_('التقييم')
    )
    license_number = models.CharField(max_length=50, blank=True,
                                       verbose_name=_('رقم الترخيص'),
                                       help_text=_("رقم ترخيص مزاولة المهنة للوكلاء العقاريين"))
    license_expiry = models.DateField(null=True, blank=True, verbose_name=_('تاريخ انتهاء الترخيص'))
    preferred_locations = models.TextField(blank=True,
                                           verbose_name=_('المواقع المفضلة'),
                                           help_text=_("قائمة المواقع المفضلة مفصولة بفواصل (أو JSON)")) # Suggest JSON?
    property_preferences = models.TextField(blank=True,
                                            verbose_name=_('تفضيلات العقارات'),
                                            help_text=_("تفضيلات نوع العقار للمشترين (أو JSON)")) # Suggest JSON?

    class Meta:
        verbose_name = _('ملف تعريف المستخدم')
        verbose_name_plural = _('ملفات تعريف المستخدمين')
        app_label = 'accounts' # Explicitly set the app_label

    def __str__(self):
        return f"Profile for {self.user.email}"
