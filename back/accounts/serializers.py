# Path: accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, List, Optional # Added Optional
from .models import Role, UserProfile
from django.db import transaction
import logging # Added logging

logger = logging.getLogger(__name__)
User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying Role information. Read-only.
    """
    display_name = serializers.CharField(source='get_name_display', read_only=True, label=_('اسم العرض'))

    class Meta:
        model = Role
        # Only include fields relevant for display purposes
        fields = ('name', 'display_name', 'description')
        read_only_fields = fields # All fields are read-only
        labels = {
            'name': _('الاسم الرمزي للدور'), # Clarified label
            'description': _('الوصف'),
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration. Handles password validation,
    confirmation, and initial role assignment.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password], # Use Django's password validators
        style={'input_type': 'password'},
        label=_('كلمة المرور')
    )
    # Field name should match what frontend sends (e.g., confirm_password or password_confirmation)
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label=_('تأكيد كلمة المرور')
    )
    first_name = serializers.CharField(required=True, max_length=150, label=_('الاسم الأول')) # Added max_length
    last_name = serializers.CharField(required=True, max_length=150, label=_('اسم العائلة')) # Added max_length
    email = serializers.EmailField(required=True, label=_('البريد الإلكتروني')) # Explicitly defined for clarity
    role = serializers.ChoiceField(
        choices=[(r[0], r[1]) for r in Role.ROLE_CHOICES if r[0] != Role.ADMIN], # Exclude Admin from choices
        required=True,
        write_only=True,
        help_text=_("اختر دور المستخدم الأساسي عند التسجيل."),
        label=_('الدور')
    )

    class Meta:
        model = User
        fields = (
            # Keep fields minimal for registration endpoint
            'email',
            'password',
            'confirm_password',
            'first_name',
            'last_name',
            'role',
            # Optional fields during registration:
            'phone_number',
            'date_of_birth',
        )
        extra_kwargs = {
            # Redundant required=True if field defined explicitly above
            # 'first_name': {'required': True},
            # 'last_name': {'required': True},
            # 'email': {'required': True, 'label': _('البريد الإلكتروني')},
            'phone_number': {'label': _('رقم الهاتف'), 'required': False},
            'date_of_birth': {'label': _('تاريخ الميلاد'), 'required': False},
        }

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate passwords match and role assignment is allowed.
        """
        # Check password confirmation
        password = attrs.get('password')
        confirm_password = attrs.pop('confirm_password', None) # Pop here is cleaner

        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({
                # Using a non-field error or targeting 'confirm_password' might be better UI-wise
                "confirm_password": _("حقلي كلمة المرور غير متطابقين.")
            })

        # Double-check role is not Admin (already filtered in choices, but good practice)
        role = attrs.get('role')
        if role == Role.ADMIN:
            raise serializers.ValidationError({
                "role": _("لا يمكن تعيين دور المشرف أثناء التسجيل.")
            })

        return attrs # Return attributes without confirm_password

    @transaction.atomic # Ensure user creation and role assignment are atomic
    def create(self, validated_data: Dict[str, Any]) -> User:
        """
        Create the user and assign the specified role.
        """
        role_name = validated_data.pop('role')

        try:
            # User.objects.create_user handles password hashing
            user = User.objects.create_user(**validated_data)

            # Assign the selected role
            # Use add_role method from CustomUser model if it handles get_or_create
            # user.add_role(role_name)
            # Or handle here:
            role_obj, created = Role.objects.get_or_create(name=role_name)
            user.roles.add(role_obj)
            logger.info(f"User '{user.email}' created successfully with role '{role_name}'.")

        except Exception as e:
            logger.error(f"Error during user registration for email {validated_data.get('email')}: {e}", exc_info=True)
            # Transaction ensures rollback, no need for user.delete()
            # Raise a generic error or re-raise specific ones if needed
            raise serializers.ValidationError(_("حدث خطأ أثناء إنشاء المستخدم. يرجى المحاولة مرة أخرى."))

        return user


class RoleInfoSerializer(serializers.Serializer):
    """
    Simple serializer for representing role code and display name.
    Used nested within UserProfileSerializer.
    """
    code = serializers.CharField(source='name', label=_('الرمز')) # Source from Role model 'name' field
    name = serializers.CharField(source='get_name_display', label=_('الاسم')) # Source from Role model method

    class Meta:
        # Not strictly needed for Serializer, but helps clarity
        fields = ('code', 'name')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving comprehensive user and profile information. READ-ONLY focus.
    Prefetch 'profile' and 'roles' in the view for efficiency.
    """
    # User fields (direct from CustomUser)
    email = serializers.EmailField(read_only=True, label=_('البريد الإلكتروني'))
    first_name = serializers.CharField(read_only=True, label=_('الاسم الأول'))
    last_name = serializers.CharField(read_only=True, label=_('اسم العائلة'))
    phone_number = serializers.CharField(read_only=True, label=_('رقم الهاتف'))
    date_of_birth = serializers.DateField(read_only=True, label=_('تاريخ الميلاد'))
    is_verified = serializers.BooleanField(read_only=True, label=_('تم التحقق'))
    date_joined = serializers.DateTimeField(read_only=True, label=_('تاريخ الانضمام'))
    is_active = serializers.BooleanField(read_only=True, label=_('نشط'))
    avatar_url = serializers.SerializerMethodField(label=_('رابط الصورة الرمزية')) # Keep using SerializerMethodField for full URL

    # Role information (using nested RoleInfoSerializer for efficiency)
    # Ensure 'roles' are prefetched in the view: User.objects.prefetch_related('roles')
    roles = RoleInfoSerializer(many=True, read_only=True, label=_('الأدوار'))
    primary_role = serializers.SerializerMethodField(label=_('الدور الأساسي'))

    # Profile fields (accessed via 'profile' relation)
    # Ensure 'profile' is selected/prefetched in the view: User.objects.select_related('profile')
    bio = serializers.CharField(source='profile.bio', read_only=True, allow_null=True, label=_('نبذة شخصية'))
    company_name = serializers.CharField(source='profile.company_name', read_only=True, allow_null=True, label=_('اسم الشركة'))
    company_registration = serializers.CharField(source='profile.company_registration', read_only=True, allow_null=True, label=_('رقم تسجيل الشركة'))
    tax_id = serializers.CharField(source='profile.tax_id', read_only=True, allow_null=True, label=_('الرقم الضريبي'))
    address = serializers.CharField(source='profile.address', read_only=True, allow_null=True, label=_('العنوان'))
    city = serializers.CharField(source='profile.city', read_only=True, allow_null=True, label=_('المدينة'))
    state = serializers.CharField(source='profile.state', read_only=True, allow_null=True, label=_('المحافظة/الولاية'))
    postal_code = serializers.CharField(source='profile.postal_code', read_only=True, allow_null=True, label=_('الرمز البريدي'))
    country = serializers.CharField(source='profile.country', read_only=True, allow_null=True, label=_('الدولة'))
    credit_limit = serializers.DecimalField(source='profile.credit_limit', max_digits=15, decimal_places=2, read_only=True, label=_('الحد الائتماني'))
    rating = serializers.DecimalField(source='profile.rating', max_digits=3, decimal_places=2, read_only=True, allow_null=True, label=_('التقييم'))
    license_number = serializers.CharField(source='profile.license_number', read_only=True, allow_null=True, label=_('رقم الترخيص'))
    license_expiry = serializers.DateField(source='profile.license_expiry', read_only=True, allow_null=True, label=_('تاريخ انتهاء الترخيص'))
    preferred_locations = serializers.CharField(source='profile.preferred_locations', read_only=True, allow_null=True, label=_('المواقع المفضلة'))
    property_preferences = serializers.CharField(source='profile.property_preferences', read_only=True, allow_null=True, label=_('تفضيلات العقارات'))

    class Meta:
        model = User
        fields = (
            'id', 'uuid', # Include UUID if used externally
            'email', 'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'avatar_url', # Use the method field for URL
            'is_verified', 'is_active', 'date_joined',
            'primary_role', 'roles', # Use optimized role fields
            # Profile fields (will be null/default if no profile)
            'bio', 'company_name', 'company_registration', 'tax_id',
            'address', 'city', 'state', 'postal_code', 'country',
            'license_number', 'license_expiry',
            'preferred_locations', 'property_preferences',
            'credit_limit', 'rating',
        )
        read_only_fields = fields # This serializer is read-only

    def get_avatar_url(self, obj: User) -> Optional[str]:
        """Generate absolute URL for the avatar."""
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url') and request:
            try:
                return request.build_absolute_uri(obj.avatar.url)
            except Exception as e:
                logger.warning(f"Could not build avatar URL for user {obj.id}: {e}")
        return None

    def get_primary_role(self, obj: User) -> Optional[Dict[str, str]]:
        """Return the user's primary role using the optimized roles data."""
        # Assumes 'roles' M2M field on 'obj' contains prefetched Role objects
        primary_role_name = obj.primary_role # Get the primary role name (e.g., 'admin')
        if not primary_role_name:
            return None

        # Find the corresponding Role object from the prefetched roles
        # This avoids hitting the DB again inside the loop
        for role in obj.roles.all(): # Access prefetched roles
            if role.name == primary_role_name:
                return RoleInfoSerializer(role).data # Use the nested serializer
        return None # Should not happen if primary_role exists, but safety check

    def to_representation(self, instance: User) -> Dict[str, Any]:
        """Ensure profile fields have defaults if profile relation doesn't exist."""
        # Get base representation from User model fields
        rep = super().to_representation(instance)

        # Check if profile exists and add profile fields with defaults
        profile = getattr(instance, 'profile', None)
        profile_fields = [
            'bio', 'company_name', 'company_registration', 'tax_id', 'address',
            'city', 'state', 'postal_code', 'country', 'license_number',
            'preferred_locations', 'property_preferences'
        ]
        decimal_fields = ['credit_limit', 'rating']
        date_fields = ['license_expiry']

        for field in profile_fields:
            rep[field] = getattr(profile, field, '') if profile else ''
        for field in decimal_fields:
             # Ensure correct default, e.g., None or 0.00
            rep[field] = getattr(profile, field, None) if profile else (0.0 if field == 'credit_limit' else None)
        for field in date_fields:
            rep[field] = getattr(profile, field, None) if profile else None

        return rep


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating User and associated UserProfile fields.
    Intended for use with PATCH requests for partial updates.
    """
    # --- User Fields (Updatable) ---
    # Make fields not required for PATCH
    first_name = serializers.CharField(required=False, max_length=150, label=_('الاسم الأول'))
    last_name = serializers.CharField(required=False, max_length=150, label=_('اسم العائلة'))
    phone_number = serializers.CharField(required=False, allow_blank=True, label=_('رقم الهاتف')) # Allow blank
    date_of_birth = serializers.DateField(required=False, allow_null=True, label=_('تاريخ الميلاد')) # Allow null
    avatar = serializers.ImageField(required=False, allow_null=True, label=_('الصورة الشخصية')) # Allow null to clear

    # --- Profile Fields (Updatable, access via source) ---
    # Define profile fields directly here for update, make them optional
    bio = serializers.CharField(source='profile.bio', required=False, allow_blank=True, label=_('نبذة شخصية'))
    company_name = serializers.CharField(source='profile.company_name', required=False, allow_blank=True, label=_('اسم الشركة'))
    company_registration = serializers.CharField(source='profile.company_registration', required=False, allow_blank=True, allow_null=True, label=_('رقم تسجيل الشركة')) # Ensure model allows null
    tax_id = serializers.CharField(source='profile.tax_id', required=False, allow_blank=True, label=_('الرقم الضريبي'))
    address = serializers.CharField(source='profile.address', required=False, allow_blank=True, label=_('العنوان'))
    city = serializers.CharField(source='profile.city', required=False, allow_blank=True, label=_('المدينة'))
    state = serializers.CharField(source='profile.state', required=False, allow_blank=True, label=_('المحافظة/الولاية'))
    postal_code = serializers.CharField(source='profile.postal_code', required=False, allow_blank=True, label=_('الرمز البريدي'))
    country = serializers.CharField(source='profile.country', required=False, allow_blank=True, label=_('الدولة'))
    license_number = serializers.CharField(source='profile.license_number', required=False, allow_blank=True, label=_('رقم الترخيص'))
    license_expiry = serializers.DateField(source='profile.license_expiry', required=False, allow_null=True, label=_('تاريخ انتهاء الترخيص'))
    preferred_locations = serializers.CharField(source='profile.preferred_locations', required=False, allow_blank=True, label=_('المواقع المفضلة'))
    property_preferences = serializers.CharField(source='profile.property_preferences', required=False, allow_blank=True, label=_('تفضيلات العقارات'))

    # --- Role Update Field (Optional) ---
    # Use for *replacing* roles entirely during update. Use UserRoleUpdateSerializer for add/remove.
    roles = serializers.MultipleChoiceField(
        choices=Role.ROLE_CHOICES,
        required=False, # Make roles optional for profile update
        write_only=True, # Roles are usually read via UserProfileSerializer
        help_text=_("استبدل أدوار المستخدم الحالية بهذه القائمة (يتطلب صلاحيات مناسبة)."),
        label=_('الأدوار (استبدال)')
    )

    class Meta:
        model = User
        # List all fields that can be updated via this serializer
        fields = (
            'first_name', 'last_name', 'phone_number', 'date_of_birth', 'avatar',
            # Profile fields sourced from 'profile' relation
            'bio', 'company_name', 'company_registration', 'tax_id', 'address',
            'city', 'state', 'postal_code', 'country', 'license_number',
            'license_expiry', 'preferred_locations', 'property_preferences',
            # Role replacement field
            'roles',
        )
        # No read_only_fields needed as this is purely for updates (write)

    def validate_roles(self, roles: List[str]) -> List[str]:
        """
        Validate role assignment permissions. Only Admins can assign Admin role.
        """
        request = self.context.get('request')
        if not request or not request.user:
             # Should not happen if used with authenticated views, but safety check
             raise serializers.ValidationError(_("لا يمكن التحقق من صلاحيات المستخدم."))

        # Prevent non-admins from assigning the ADMIN role
        if Role.ADMIN in roles and not request.user.has_role(Role.ADMIN):
            raise serializers.ValidationError(
                _("يمكن تعيين دور المشرف فقط بواسطة المشرفين الحاليين.")
            )
        # Add other role validation logic if needed (e.g., preventing self-removal of last admin)
        return roles

    @transaction.atomic
    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        """
        Update User instance and related UserProfile instance.
        Handles nested profile fields and role replacement.
        """
        # Ensure profile exists before attempting to update profile fields
        profile, _ = UserProfile.objects.get_or_create(user=instance)

        # Separate profile data from user data
        profile_data = {}
        user_data = {}
        role_data = None

        if 'roles' in validated_data:
            role_data = validated_data.pop('roles')

        # Iterate through validated_data to populate user_data and profile_data
        for field_name, value in validated_data.items():
            # Check if the field belongs to the profile via 'source'
            field_obj = self.fields.get(field_name)
            if field_obj and field_obj.source and field_obj.source.startswith('profile.'):
                profile_field_name = field_obj.source.split('.')[-1]
                profile_data[profile_field_name] = value
            else:
                # Assume it's a direct field on the User model
                user_data[field_name] = value

        # Update User fields
        for attr, value in user_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=user_data.keys()) # Update only specified user fields

        # Update Profile fields
        if profile_data:
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save(update_fields=profile_data.keys()) # Update only specified profile fields

        # Handle role replacement if 'roles' was provided
        if role_data is not None:
            # Clear existing roles before adding new ones
            instance.roles.clear()
            roles_to_add = Role.objects.filter(name__in=role_data)
            instance.roles.add(*roles_to_add) # Efficiently add multiple roles
            logger.info(f"Roles updated for user '{instance.email}' to: {role_data}")

        # Refresh instance from DB to reflect all changes? Optional.
        # instance.refresh_from_db()
        return instance


class UserRoleUpdateSerializer(serializers.Serializer):
    """
    Serializer specifically for adding or removing a *single* role from a user.
    Requires view logic to perform the actual update on the User instance.
    """
    action = serializers.ChoiceField(
        choices=[('add', _('إضافة')), ('remove', _('إزالة'))], # Use tuples for choices
        required=True,
        help_text=_("اختر 'add' لإضافة الدور أو 'remove' لإزالته."),
        label=_('الإجراء')
    )
    role = serializers.ChoiceField(
        choices=Role.ROLE_CHOICES, # Use choices from model
        required=True,
        help_text=_("الدور المحدد الذي سيتم إضافته أو إزالته."),
        label=_('الدور')
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate permissions for modifying roles, especially the Admin role.
        """
        role_name = attrs.get('role')
        request = self.context.get('request')

        if not request or not request.user:
            raise serializers.ValidationError(_("لا يمكن التحقق من صلاحيات المستخدم."))

        # Prevent non-admins from modifying the ADMIN role
        if role_name == Role.ADMIN and not request.user.has_role(Role.ADMIN):
            raise serializers.ValidationError({
                "role": _("يمكن تعديل دور المشرف فقط بواسطة المشرفين الحاليين.")
            })

        # Optional: Prevent removing the last admin role? Needs more context.
        # target_user = self.context.get('target_user') # View needs to pass the user being modified
        # if action == 'remove' and role_name == Role.ADMIN and target_user:
        #    if target_user.roles.filter(name=Role.ADMIN).count() == 1:
        #        # Check if there are other admins before allowing removal
        #        if User.objects.filter(roles__name=Role.ADMIN).count() <= 1:
        #             raise serializers.ValidationError(_("Cannot remove the last administrator."))

        return attrs

    # NOTE: This serializer does not implement .save() or .update().
    # The view using this serializer is responsible for:
    # 1. Retrieving the target User instance.
    # 2. Instantiating this serializer with context (request, target_user).
    # 3. Calling is_valid(raise_exception=True).
    # 4. Performing the user.roles.add(role) or user.roles.remove(role) operation based on validated_data.
