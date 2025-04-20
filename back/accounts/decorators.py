# base/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

def role_required(roles):
    """Function decorator for requiring specific roles"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")

            user_roles = request.user.role_names
            if not any(role in user_roles for role in roles):
                raise PermissionDenied("Insufficient permissions")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Permission class for use with class-based views
class RoleRequiredPermission(BasePermission):
    """Permission class that requires specific roles"""

    def __init__(self, roles):
        self.roles = roles

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_roles = request.user.role_names
        return any(role in user_roles for role in self.roles)
