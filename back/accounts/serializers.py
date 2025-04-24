from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, Optional
from .models import UserProfile
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password validation"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = (
            'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone_number': {'required': False},
            'date_of_birth': {'required': False},
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.pop('confirm_password', None):
            raise serializers.ValidationError({
                "confirm_password": _("Passwords do not match.")
            })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        logger.info(f"User '{user.email}' created successfully")
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving comprehensive user and profile information"""
    # User fields
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    date_of_birth = serializers.DateField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    # Profile fields
    bio = serializers.CharField(source='profile.bio', read_only=True, allow_null=True)
    company_name = serializers.CharField(source='profile.company_name', read_only=True, allow_null=True)
    company_registration = serializers.CharField(source='profile.company_registration', read_only=True, allow_null=True)
    tax_id = serializers.CharField(source='profile.tax_id', read_only=True, allow_null=True)
    address = serializers.CharField(source='profile.address', read_only=True, allow_null=True)
    city = serializers.CharField(source='profile.city', read_only=True, allow_null=True)
    state = serializers.CharField(source='profile.state', read_only=True, allow_null=True)
    postal_code = serializers.CharField(source='profile.postal_code', read_only=True, allow_null=True)
    country = serializers.CharField(source='profile.country', read_only=True, allow_null=True)
    credit_limit = serializers.DecimalField(source='profile.credit_limit', max_digits=15, decimal_places=2, read_only=True)
    rating = serializers.DecimalField(source='profile.rating', max_digits=3, decimal_places=2, read_only=True, allow_null=True)
    license_number = serializers.CharField(source='profile.license_number', read_only=True, allow_null=True)
    license_expiry = serializers.DateField(source='profile.license_expiry', read_only=True, allow_null=True)
    preferred_locations = serializers.CharField(source='profile.preferred_locations', read_only=True, allow_null=True)
    property_preferences = serializers.CharField(source='profile.property_preferences', read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'uuid',
            'email', 'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'avatar_url',
            'is_verified', 'is_active', 'is_staff', 'date_joined',
            # Profile fields
            'bio', 'company_name', 'company_registration', 'tax_id',
            'address', 'city', 'state', 'postal_code', 'country',
            'license_number', 'license_expiry',
            'preferred_locations', 'property_preferences',
            'credit_limit', 'rating',
        )
        read_only_fields = fields

    def get_avatar_url(self, obj):
        """Generate absolute URL for the avatar."""
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url') and request:
            try:
                return request.build_absolute_uri(obj.avatar.url)
            except Exception as e:
                logger.warning(f"Could not build avatar URL: {e}")
        return None

    def to_representation(self, instance):
        """Ensure profile fields have defaults if profile relation doesn't exist."""
        rep = super().to_representation(instance)
        profile = getattr(instance, 'profile', None)

        # Set defaults for different field types
        text_fields = [
            'bio', 'company_name', 'company_registration', 'tax_id', 'address',
            'city', 'state', 'postal_code', 'country', 'license_number',
            'preferred_locations', 'property_preferences'
        ]
        decimal_fields = ['credit_limit', 'rating']
        date_fields = ['license_expiry']

        for field in text_fields:
            rep[field] = getattr(profile, field, '') if profile else ''

        for field in decimal_fields:
            rep[field] = getattr(profile, field, None) if profile else (0.0 if field == 'credit_limit' else None)

        for field in date_fields:
            rep[field] = getattr(profile, field, None) if profile else None

        return rep


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating User and associated UserProfile fields"""
    # User fields (updatable)
    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    avatar = serializers.ImageField(required=False, allow_null=True)

    # Profile fields (updatable)
    bio = serializers.CharField(source='profile.bio', required=False, allow_blank=True)
    company_name = serializers.CharField(source='profile.company_name', required=False, allow_blank=True)
    company_registration = serializers.CharField(source='profile.company_registration', required=False, allow_blank=True, allow_null=True)
    tax_id = serializers.CharField(source='profile.tax_id', required=False, allow_blank=True)
    address = serializers.CharField(source='profile.address', required=False, allow_blank=True)
    city = serializers.CharField(source='profile.city', required=False, allow_blank=True)
    state = serializers.CharField(source='profile.state', required=False, allow_blank=True)
    postal_code = serializers.CharField(source='profile.postal_code', required=False, allow_blank=True)
    country = serializers.CharField(source='profile.country', required=False, allow_blank=True)
    license_number = serializers.CharField(source='profile.license_number', required=False, allow_blank=True)
    license_expiry = serializers.DateField(source='profile.license_expiry', required=False, allow_null=True)
    preferred_locations = serializers.CharField(source='profile.preferred_locations', required=False, allow_blank=True)
    property_preferences = serializers.CharField(source='profile.property_preferences', required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'phone_number', 'date_of_birth', 'avatar',
            # Profile fields
            'bio', 'company_name', 'company_registration', 'tax_id', 'address',
            'city', 'state', 'postal_code', 'country', 'license_number',
            'license_expiry', 'preferred_locations', 'property_preferences',
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update User instance and related UserProfile instance"""
        # Ensure profile exists before attempting to update profile fields
        profile, _ = UserProfile.objects.get_or_create(user=instance)

        # Separate profile data from user data
        profile_data = {}
        user_data = {}

        # Sort validated data into user and profile fields
        for field_name, value in validated_data.items():
            field_obj = self.fields.get(field_name)
            if field_obj and hasattr(field_obj, 'source') and field_obj.source and field_obj.source.startswith('profile.'):
                profile_field_name = field_obj.source.split('.')[-1]
                profile_data[profile_field_name] = value
            else:
                user_data[field_name] = value

        # Update User fields
        for attr, value in user_data.items():
            setattr(instance, attr, value)
        if user_data:
            instance.save(update_fields=user_data.keys())

        # Update Profile fields
        if profile_data:
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save(update_fields=profile_data.keys())

        return instance

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
