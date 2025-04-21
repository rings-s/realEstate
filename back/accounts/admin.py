# Path: accounts/admin.py
# This file configures the Django admin interface for user accounts
# It includes customized forms and displays for roles and user profiles

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Role, UserProfile
from django.contrib.auth.models import Group
from base.models import Media
from django.contrib.contenttypes.admin import GenericTabularInline


class MediaInline(GenericTabularInline):
    model = Media
    extra = 1
    fields = ('file', 'media_type', 'is_cover', 'order')
    readonly_fields = ('uploaded_at',)


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile to be displayed on the user admin page
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('ملف تعريف المستخدم')
    fieldsets = (
        (_('معلومات الملف الشخصي'), {
            'fields': ('bio', 'company_name', 'company_registration', 'tax_id')
        }),
        (_('معلومات العنوان'), {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        (_('معلومات مالية'), {
            'fields': ('credit_limit', 'rating')
        }),
        (_('معلومات المهنة'), {
            'fields': ('license_number', 'license_expiry')
        }),
        (_('تفضيلات'), {
            'fields': ('preferred_locations', 'property_preferences')
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Role model
    """
    list_display = ('get_name_display', 'description', 'created_at', 'updated_at')
    fieldsets = (
        (_('معلومات الدور'), {
            'fields': ('name', 'description')
        }),
        (_('الصلاحيات'), {
            'fields': ('permissions',)
        }),
    )
    filter_horizontal = ('permissions',)
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def get_name_display(self, obj):
        """
        Format the role name for display in the admin
        """
        return obj.get_name_display()
    get_name_display.short_description = _('الاسم')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for the CustomUser model
    Includes both the UUID and regular ID fields
    """
    list_display = ('id', 'uuid', 'email', 'first_name', 'last_name', 'primary_role', 'is_active', 'is_verified', 'date_joined')
    list_filter = ('is_active', 'is_verified', 'is_staff', 'roles')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'uuid')
    ordering = ('email',)
    readonly_fields = ('id', 'uuid',)

    fieldsets = (
        (_('معلومات الحساب'), {
            'fields': ('id', 'uuid', 'email', 'password', 'is_active', 'is_verified')
        }),
        (_('معلومات شخصية'), {
            'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth')
        }),
        (_('الأدوار والصلاحيات'), {
            'fields': ('roles', 'is_staff', 'is_superuser')
        }),
        (_('التحقق'), {
            'fields': ('verification_code', 'verification_code_created', 'reset_code', 'reset_code_created')
        }),
        (_('تواريخ'), {
            'fields': ('date_joined', 'last_login')
        }),
    )

    add_fieldsets = (
        (_('معلومات الحساب'), {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_active', 'is_verified'),
        }),
        (_('معلومات شخصية'), {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth'),
        }),
        (_('الأدوار والصلاحيات'), {
            'classes': ('wide',),
            'fields': ('roles', 'is_staff', 'is_superuser'),
        }),
    )

    filter_horizontal = ('roles', 'groups', 'user_permissions')
    inlines = [UserProfileInline, MediaInline]

    def primary_role(self, obj):
        """
        Get the user's primary role for display in the admin
        """
        return obj.primary_role or _('لا يوجد')
    primary_role.short_description = _('الدور الأساسي')


# Unregister the Group model from admin
admin.site.unregister(Group)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for the UserProfile model
    """
    list_display = ('user', 'company_name', 'city', 'country', 'credit_limit', 'rating')
    list_filter = ('city', 'country')
    search_fields = ('user__email', 'company_name', 'address', 'city')
    fieldsets = (
        (_('المستخدم'), {
            'fields': ('user',)
        }),
        (_('معلومات الملف الشخصي'), {
            'fields': ('bio', 'company_name', 'company_registration', 'tax_id')
        }),
        (_('معلومات العنوان'), {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        (_('معلومات مالية'), {
            'fields': ('credit_limit', 'rating')
        }),
        (_('معلومات المهنة'), {
            'fields': ('license_number', 'license_expiry')
        }),
        (_('تفضيلات'), {
            'fields': ('preferred_locations', 'property_preferences')
        }),
        (_('تواريخ'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [MediaInline]
