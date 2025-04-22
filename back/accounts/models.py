import os
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
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

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email is required'))
        email = self.normalize_email(email)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True'))

        with transaction.atomic():
            user = self.create_user(email, password, **extra_fields)
        return user
# --- Custom User Model ---

class CustomUser(AbstractUser):
    # Remove roles field
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_('UUID'), db_index=True)
    username = None
    email = models.EmailField(_('Email'), unique=True, db_index=True)
    first_name = models.CharField(_('First name'), max_length=150)
    last_name = models.CharField(_('Last name'), max_length=150)

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be in format: '+999999999'. Max 15 digits allowed.")
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, verbose_name=_('Phone number'))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_('Date of birth'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Verified'),
                                     help_text=_('Indicates if user has verified their email'))
    verification_code = models.CharField(max_length=6, blank=True, null=True, verbose_name=_('Verification code'))
    verification_code_created = models.DateTimeField(null=True, blank=True)
    reset_code = models.CharField(max_length=6, blank=True, null=True, verbose_name=_('Password reset code'))
    reset_code_created = models.DateTimeField(null=True, blank=True)
    avatar = models.ImageField(upload_to=user_avatar_path, null=True, blank=True, verbose_name=_('Avatar'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()


    # Keep verification and reset methods

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.uuid:
            self.uuid = uuid.uuid4()
        super().save(*args, **kwargs)

        if is_new:
            UserProfile.objects.get_or_create(user=self)
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
