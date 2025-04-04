from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from accounts.models import Role, CustomUser


# Base permission class for role-based permissions
class HasRolePermission(BasePermission):
    """
    Permission class that checks if user has any of the specified roles.
    Uses the Role model from accounts app.
    """

    def __init__(self, required_roles=None):
        self.required_roles = required_roles or []

    def has_permission(self, request, view):
        # Anonymous users don't have roles
        if not request.user.is_authenticated:
            return False

        # Staff users bypass role checks
        if request.user.is_staff or request.user.is_superuser:
            return True

        # If no specific roles are required, just require authentication
        if not self.required_roles:
            return True

        # Check if user has any of the required roles using the accounts.models.Role
        for role in self.required_roles:
            if request.user.has_role(role):
                return True

        return False


# Role-specific permission classes
class IsSellerPermission(BasePermission):
    """Permission for users with SELLER role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.has_role(Role.SELLER)
            or request.user.has_role(Role.AGENT)
            or request.user.is_staff
        )


class IsBuyerPermission(BasePermission):
    """Permission for users with BUYER role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.has_role(Role.BUYER) or request.user.is_staff
        )


class IsInspectorPermission(BasePermission):
    """Permission for users with INSPECTOR role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.has_role(Role.INSPECTOR) or request.user.is_staff
        )


class IsLegalPermission(BasePermission):
    """Permission for users with LEGAL role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.has_role(Role.LEGAL) or request.user.is_staff
        )


class IsAgentPermission(BasePermission):
    """Permission for users with AGENT role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.has_role(Role.AGENT) or request.user.is_staff
        )


class IsAppraiserPermission(BasePermission):
    """Permission for users with APPRAISER role."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.has_role(Role.APPRAISER) or request.user.is_staff
        )


# Object-based permissions
class IsPropertyOwner(BasePermission):
    """Permission for property owners."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.is_staff


class IsAuctionCreator(BasePermission):
    """Permission for auction creators."""

    def has_object_permission(self, request, view, obj):
        return (
            obj.created_by == request.user
            or obj.auctioneer == request.user
            or request.user.is_staff
        )
