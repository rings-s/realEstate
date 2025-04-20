from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, List
from .models import Role, UserProfile
from django.db import transaction

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model"""
    display_name = serializers.CharField(source='get_name_display', read_only=True, label=_('اسم العرض'))

    class Meta:
        model = Role
        fields = ('name', 'display_name', 'description')
        read_only_fields = ('name', 'display_name', 'description')
        labels = {
            'name': _('الاسم'),
            'description': _('الوصف'),
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with role assignment
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        label=_('كلمة المرور')
    )
    # Change password_confirmation to match what the frontend sends
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label=_('تأكيد كلمة المرور')
    )
    first_name = serializers.CharField(required=True, label=_('الاسم الأول'))
    last_name = serializers.CharField(required=True, label=_('اسم العائلة'))
    role = serializers.ChoiceField(
        choices=Role.ROLE_CHOICES,
        required=True,
        write_only=True,
        help_text=_("دور المستخدم الأساسي في منصة المزادات العقارية"),
        label=_('الدور')
    )

    class Meta:
        model = User
        fields = (
            'email',
            'password',
            'confirm_password',  # Changed from password_confirmation
            'first_name',
            'last_name',
            'phone_number',
            'date_of_birth',
            'role'
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True, 'label': _('البريد الإلكتروني')},
            'phone_number': {'label': _('رقم الهاتف')},
            'date_of_birth': {'label': _('تاريخ الميلاد')},
        }

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Check if password and confirm_password match
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                "password": _("حقلي كلمة المرور غير متطابقين.")
            })

        # Validate role
        role = attrs.get('role')
        if role == Role.ADMIN:
            raise serializers.ValidationError({
                "role": _("لا يمكن تعيين دور المشرف أثناء التسجيل.")
            })

        # Remove confirm_password from attrs after validation
        if 'confirm_password' in attrs:
            attrs.pop('confirm_password')

        return attrs

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> User:
        # Extract role data before creating user
        role_name = validated_data.pop('role')

        # Create user - UserProfile is automatically created by the model's save method
        user = User.objects.create_user(**validated_data)

        # Assign role using M2M relationship
        try:
            role, created = Role.objects.get_or_create(name=role_name)
            user.roles.add(role)
        except Exception as e:
            # Roll back transaction if something goes wrong
            user.delete()
            raise serializers.ValidationError({
                "role": _("خطأ في تعيين الدور: {}").format(str(e))
            })

        return user

class RoleInfoSerializer(serializers.Serializer):
    """Serializer for role information"""
    code = serializers.CharField(label=_('الرمز'))
    name = serializers.CharField(label=_('الاسم'))


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving user profile information
    Combines User and UserProfile models
    """
    avatar_url = serializers.SerializerMethodField()

    primary_role = serializers.SerializerMethodField(label=_('الدور الأساسي'))
    roles = serializers.SerializerMethodField(label=_('الأدوار'))
    company_name = serializers.CharField(source='profile.company_name', required=False, allow_null=True, allow_blank=True, label=_('اسم الشركة'))
    company_registration = serializers.CharField(source='profile.company_registration', required=False, allow_null=True, allow_blank=True, label=_('رقم تسجيل الشركة'))
    tax_id = serializers.CharField(source='profile.tax_id', required=False, allow_null=True, allow_blank=True, label=_('الرقم الضريبي'))
    address = serializers.CharField(source='profile.address', required=False, allow_null=True, allow_blank=True, label=_('العنوان'))
    city = serializers.CharField(source='profile.city', required=False, allow_null=True, allow_blank=True, label=_('المدينة'))
    state = serializers.CharField(source='profile.state', required=False, allow_null=True, allow_blank=True, label=_('المحافظة/الولاية'))
    postal_code = serializers.CharField(source='profile.postal_code', required=False, allow_null=True, allow_blank=True, label=_('الرمز البريدي'))
    country = serializers.CharField(source='profile.country', required=False, allow_null=True, allow_blank=True, label=_('الدولة'))
    bio = serializers.CharField(source='profile.bio', required=False, allow_null=True, allow_blank=True, label=_('نبذة شخصية'))
    credit_limit = serializers.DecimalField(source='profile.credit_limit', max_digits=15, decimal_places=2, read_only=True, label=_('الحد الائتماني'))
    rating = serializers.DecimalField(source='profile.rating', max_digits=3, decimal_places=2, read_only=True, allow_null=True, label=_('التقييم'))
    license_number = serializers.CharField(source='profile.license_number', required=False, allow_null=True, allow_blank=True, label=_('رقم الترخيص'))
    license_expiry = serializers.DateField(source='profile.license_expiry', required=False, allow_null=True, label=_('تاريخ انتهاء الترخيص'))
    preferred_locations = serializers.CharField(source='profile.preferred_locations', required=False, allow_null=True, allow_blank=True, label=_('المواقع المفضلة'))
    property_preferences = serializers.CharField(source='profile.property_preferences', required=False, allow_null=True, allow_blank=True, label=_('تفضيلات العقارات'))

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'date_of_birth',
            'avatar',
            'is_verified',
            'primary_role',
            'roles',
            'bio',
            'company_name',
            'company_registration',
            'tax_id',
            'address',
            'city',
            'state',
            'postal_code',
            'country',
            'license_number',
            'license_expiry',
            'preferred_locations',
            'property_preferences',
            'credit_limit',
            'rating',
            'date_joined',
            'is_active',
            'avatar_url'
        )
        read_only_fields = (
            'id',
            'email',
            'is_verified',
            'credit_limit',
            'rating',
            'date_joined',
            'is_active',
            'primary_role',
            'roles',
        )
        labels = {
            'id': _('المعرف'),
            'email': _('البريد الإلكتروني'),
            'first_name': _('الاسم الأول'),
            'last_name': _('اسم العائلة'),
            'phone_number': _('رقم الهاتف'),
            'date_of_birth': _('تاريخ الميلاد'),
            'avatar': _('الصورة الشخصية'),
            'is_verified': _('تم التحقق'),
            'date_joined': _('تاريخ الانضمام'),
            'is_active': _('نشط'),
        }

    def get_primary_role(self, obj):
        """Return the user's primary role information"""
        primary_role = obj.primary_role
        if primary_role:
            role_obj = next((r for r in obj.roles.all() if r.name == primary_role), None)
            if role_obj:
                return {
                    'code': role_obj.name,
                    'name': role_obj.get_name_display()
                }
        return None

    def get_roles(self, obj):
        """Return all roles assigned to the user"""
        roles_data = []
        for role in obj.roles.all():
            roles_data.append({
                'code': role.name,
                'name': role.get_name_display()
            })
        return roles_data

    def to_representation(self, instance):
        """Ensure profile data is handled even if profile doesn't exist"""
        rep = super().to_representation(instance)

        # Default values for profile fields if profile doesn't exist
        if not hasattr(instance, 'profile') or not instance.profile:
            profile_fields = [
                'bio', 'company_name', 'company_registration', 'tax_id',
                'address', 'city', 'state', 'postal_code', 'country',
                'license_number', 'preferred_locations', 'property_preferences'
            ]
            for field in profile_fields:
                rep[field] = ''
            rep['credit_limit'] = 0
            rep['rating'] = None
            rep['license_expiry'] = None

        return rep

    def get_avatar_url(self, obj):
            request = self.context.get('request')
            if obj.avatar and request:
                return request.build_absolute_uri(obj.avatar.url)
            return None


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information specific to real estate platform
    """
    bio = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('نبذة شخصية'))
    company_name = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('اسم الشركة'))
    company_registration = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('رقم تسجيل الشركة'))
    tax_id = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('الرقم الضريبي'))
    address = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('العنوان'))
    city = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('المدينة'))
    state = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('المحافظة/الولاية'))
    postal_code = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('الرمز البريدي'))
    country = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('الدولة'))
    license_number = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('رقم الترخيص'))
    license_expiry = serializers.DateField(write_only=True, required=False, allow_null=True, label=_('تاريخ انتهاء الترخيص'))
    preferred_locations = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('المواقع المفضلة'))
    property_preferences = serializers.CharField(write_only=True, required=False, allow_blank=True, label=_('تفضيلات العقارات'))
    roles = serializers.MultipleChoiceField(
        choices=Role.ROLE_CHOICES,
        required=False,
        write_only=True,
        help_text=_("أدوار المستخدم في منصة المزادات العقارية"),
        label=_('الأدوار')
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'phone_number',
            'date_of_birth',
            'avatar',
            'bio',
            'company_name',
            'company_registration',
            'tax_id',
            'address',
            'city',
            'state',
            'postal_code',
            'country',
            'license_number',
            'license_expiry',
            'preferred_locations',
            'property_preferences',
            'roles',
        )
        labels = {
            'first_name': _('الاسم الأول'),
            'last_name': _('اسم العائلة'),
            'phone_number': _('رقم الهاتف'),
            'date_of_birth': _('تاريخ الميلاد'),
            'avatar': _('الصورة الشخصية'),
        }

    def validate_roles(self, roles):
        """Validate roles to prevent unauthorized role assignment"""
        # Only admins can assign the admin role
        request = self.context.get('request')
        if Role.ADMIN in roles and (not request or not request.user.has_role(Role.ADMIN)):
            raise serializers.ValidationError(
                _("يمكن تعيين دور المشرف فقط بواسطة المشرفين الحاليين.")
            )
        return roles

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update user and related profile
        """
        # Extract and handle roles if provided
        if 'roles' in validated_data:
            role_names = validated_data.pop('roles')

            # Clear existing roles
            instance.roles.clear()

            # Add new roles
            for role_name in role_names:
                role, created = Role.objects.get_or_create(name=role_name)
                instance.roles.add(role)

        # Extract profile fields
        profile_fields = {
            'bio': validated_data.pop('bio', None),
            'company_name': validated_data.pop('company_name', None),
            'company_registration': validated_data.pop('company_registration', None),
            'tax_id': validated_data.pop('tax_id', None),
            'address': validated_data.pop('address', None),
            'city': validated_data.pop('city', None),
            'state': validated_data.pop('state', None),
            'postal_code': validated_data.pop('postal_code', None),
            'country': validated_data.pop('country', None),
            'license_number': validated_data.pop('license_number', None),
            'license_expiry': validated_data.pop('license_expiry', None),
            'preferred_locations': validated_data.pop('preferred_locations', None),
            'property_preferences': validated_data.pop('property_preferences', None),
        }

        # Remove None values (fields not provided in the update)
        profile_fields = {k: v for k, v in profile_fields.items() if v is not None}

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or create profile
        if profile_fields:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_fields.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class UserRoleUpdateSerializer(serializers.Serializer):
    """
    Serializer for adding or removing roles from a user
    """
    action = serializers.ChoiceField(
        choices=['add', 'remove'],
        required=True,
        help_text=_("ما إذا كان سيتم إضافة أو إزالة الدور"),
        label=_('الإجراء')
    )
    role = serializers.ChoiceField(
        choices=Role.ROLE_CHOICES,
        required=True,
        help_text=_("الدور المراد إضافته أو إزالته"),
        label=_('الدور')
    )

    def validate(self, attrs):
        action = attrs.get('action')
        role_name = attrs.get('role')

        # Only admins can manipulate the admin role
        if role_name == Role.ADMIN:
            request = self.context.get('request')
            if not request or not request.user.has_role(Role.ADMIN):
                raise serializers.ValidationError({
                    "role": _("يمكن تعديل دور المشرف فقط بواسطة المشرفين الحاليين.")
                })

        return attrs
