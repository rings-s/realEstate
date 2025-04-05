from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission

class HasRolePermission(BasePermission):
    """Check if user has any of the specified roles"""

    def __init__(self, required_roles=None):
        self.required_roles = required_roles or []

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        if not self.required_roles:
            return True
        return any(request.user.has_role(role) for role in self.required_roles)

# Role permission factory for DRY role creation
def role_permission_factory(role_name):
    """Create role-specific permission classes"""
    class RolePermission(BasePermission):
        def has_permission(self, request, view):
            return request.user.is_authenticated and (
                request.user.has_role(role_name) or
                request.user.is_staff
            )

    RolePermission.__name__ = f"Is{role_name.capitalize()}Permission"
    RolePermission.__doc__ = f"Permission for users with {role_name.upper()} role."
    return RolePermission

# Generate common role permissions
IsSellerPermission = role_permission_factory('seller')
IsBuyerPermission = role_permission_factory('buyer')
IsInspectorPermission = role_permission_factory('inspector')
IsLegalPermission = role_permission_factory('legal')
IsAgentPermission = role_permission_factory('agent')
IsAppraiserPermission = role_permission_factory('appraiser')

# Object owner permissions
class IsObjectOwner(BasePermission):
    """Generic permission for object owners"""
    owner_field = 'owner'  # Default owner field

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, self.owner_field, None)
        return owner == request.user or request.user.is_staff

class IsPropertyOwner(IsObjectOwner):
    """Permission for property owners"""
    pass

class IsAuctionCreator(IsObjectOwner):
    """Permission for auction creators"""
    def has_object_permission(self, request, view, obj):
        return (obj.created_by == request.user or
                obj.auctioneer == request.user or
                request.user.is_staff)
