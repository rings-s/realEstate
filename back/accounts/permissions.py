# accounts/permissions.py
from rest_framework.permissions import BasePermission
from django.utils.translation import gettext_lazy as _

class IsOwnerOrAdmin(BasePermission):
    """Allows access only to object owner or admin users"""
    message = _('You must be the owner of this object or an admin.')

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        return obj == request.user

class IsAdminUser(BasePermission):
    """Allows access only to admin users"""
    message = _('You must be an administrator to perform this action.')

    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class IsVerifiedUser(BasePermission):
    """Allows access only to email-verified users"""
    message = _('You must verify your email address to perform this action.')

    def has_permission(self, request, view):
        return request.user and request.user.is_verified
