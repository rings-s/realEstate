# Path: accounts/permissions.py (assuming rename from moderaters.py)
# Contains decorators and DRF permission classes for role-based access control

from functools import wraps
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework import exceptions # Import DRF exceptions
from django.utils.translation import gettext_lazy as _


# --- Function Decorator ---
def role_required(roles):
    """
    Decorator for Django views (function-based) that checks if the logged-in
    user has at least one of the specified roles.

    Usage:
        @role_required(['admin', 'agent'])
        def my_view(request):
            ...
    """
    if isinstance(roles, str): # Allow passing a single role string
        roles = [roles]
    required_role_set = set(roles)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                # Or raise AuthenticationFailed for DRF consistency if used in API views
                raise PermissionDenied(_("Authentication required."))

            # Assumes request.user is CustomUser instance with 'role_names' property
            user_roles = getattr(request.user, 'role_names', [])
            if not required_role_set.intersection(user_roles):
                raise PermissionDenied(_("You do not have permission to perform this action."))

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# --- DRF Permission Class ---
class RoleRequiredPermission(BasePermission):
    """
    DRF Permission class that checks if the authenticated user has
    at least one of the required roles defined in the view.

    Usage in a DRF ViewSet or APIView:
        from .permissions import RoleRequiredPermission

        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, RoleRequiredPermission]
            required_roles = ['admin', 'agent'] # Define required roles here
            ...

            # Optional: Override get_required_roles for dynamic roles
            # def get_required_roles(self):
            #    if self.action == 'destroy':
            #        return ['admin']
            #    return ['admin', 'agent']
    """
    message = _('You do not have permission to perform this action based on your role.')

    # Default required roles (can be overridden in the view)
    required_roles = []

    def get_required_roles(self, request, view):
        """
        Helper method to get required roles, allowing views to override.
        """
        return getattr(view, 'required_roles', self.required_roles)

    def has_permission(self, request, view):
        # Authentication check should ideally be handled by IsAuthenticated permission class first
        if not request.user or not request.user.is_authenticated:
             # Although IsAuthenticated usually runs first, double-check here.
             # Returning False implies authentication failure if IsAuthenticated wasn't used.
             # raise exceptions.NotAuthenticated() # More explicit for DRF
            return False

        # Get required roles from the view or use default
        required = self.get_required_roles(request, view)
        if not required:
            # If no roles are specified as required, allow access (or deny if default should be restrictive)
            # logger.warning(f"No required_roles defined for view {view.__class__.__name__}")
            return True # Or False, depending on desired default behavior

        required_role_set = set(required)

        # Assumes request.user is CustomUser instance with 'role_names' property
        user_roles = getattr(request.user, 'role_names', [])
        if not user_roles:
             # User is authenticated but has no roles assigned via the 'roles' M2M field
            return False

        # Check for intersection between user's roles and required roles
        if not required_role_set.intersection(user_roles):
            return False # Permission denied

        return True # Permission granted

# Example of a more specific permission class (inherits the logic)
class IsAdminUser(RoleRequiredPermission):
     required_roles = ['admin']
     message = _('Only administrators can perform this action.')

class IsSellerUser(RoleRequiredPermission):
     required_roles = ['seller']
     message = _('Only sellers can perform this action.')

# You could also create combined permissions like IsAdminOrAgent
class IsAdminOrAgentUser(RoleRequiredPermission):
     required_roles = ['admin', 'agent']
