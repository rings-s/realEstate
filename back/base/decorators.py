import functools
import time
import logging
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from .utils import check_user_permission, check_auction_status
from .models import RoleChoices

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# View Decorators
# -------------------------------------------------------------------------

def permission_required(permission_name):
    """
    Decorator requiring specific permission for view access.

    Args:
        permission_name: Permission needed

    Returns:
        Decorated function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check authentication
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': _('Please log in to access this page.')}, status=403)
                return redirect(settings.LOGIN_URL)

            # Check permission
            if not check_user_permission(request.user, permission_name):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': _('Insufficient permissions to access this page.')}, status=403)
                raise PermissionDenied(_('Insufficient permissions to access this page.'))

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def verified_user_required(view_func):
    """Decorator requiring verified user status"""
    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check authentication
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': _('Please log in to access this page.')}, status=403)
            return redirect(settings.LOGIN_URL)

        # Check verification
        if not request.user.is_verified:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': _('Account verification required for this page.')}, status=403)
            return redirect('accounts:verification_required')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def property_owner_required(model=None, pk_url_kwarg='pk'):
    """Decorator requiring property ownership"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check authentication
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': _('Please log in to access this page.')}, status=403)
                return redirect(settings.LOGIN_URL)

            # Staff bypass
            if request.user.is_staff or (hasattr(request.user, 'has_role') and
                                        request.user.has_role(RoleChoices.ADMIN)):
                return view_func(request, *args, **kwargs)

            # Get primary key
            pk = kwargs.get(pk_url_kwarg)
            if not pk:
                raise Http404(_('No property ID provided.'))

            # Determine model
            model_class = model
            if model_class is None:
                if hasattr(view_func, 'view_class'):
                    model_class = view_func.view_class.model
                if model_class is None:
                    from .models import Property
                    model_class = Property

            # Get object
            try:
                obj = model_class.objects.get(pk=pk)
            except model_class.DoesNotExist:
                raise Http404(_('Property not found.'))

            # Check ownership
            owner_field = 'owner' if hasattr(obj, 'owner') else 'user'
            owner = getattr(obj, owner_field, None)

            if owner != request.user:
                # Check if user is an agent for the owner (if applicable)
                is_agent = False
                if hasattr(request.user, 'has_role') and request.user.has_role(RoleChoices.AGENT):
                    # This implementation would need to check agent-client relationships
                    # Example: is_agent = AgentClientRelationship.objects.filter(agent=request.user, client=owner).exists()
                    pass

                if not is_agent:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': _('This property can only be accessed by the owner or authorized agent.')},
                                           status=403)
                    raise PermissionDenied(_('This property can only be accessed by the owner or authorized agent.'))

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def auction_status_required(statuses, redirect_url=None):
    """Decorator requiring specific auction status"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get auction ID
            auction_id = kwargs.get('auction_id') or kwargs.get('pk')
            if not auction_id:
                return view_func(request, *args, **kwargs)

            # Get auction
            from .models import Auction
            try:
                auction = Auction.objects.get(pk=auction_id)
            except Auction.DoesNotExist:
                raise Http404(_('Auction not found.'))

            # Check status
            current_status = check_auction_status(auction)
            if current_status not in statuses:
                error_msg = _('This auction cannot be accessed in its current state.')

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': error_msg}, status=403)

                if redirect_url:
                    return redirect(redirect_url)

                raise PermissionDenied(error_msg)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# -------------------------------------------------------------------------
# API View Decorators
# -------------------------------------------------------------------------

def api_permission_required(permission_name):
    """API decorator requiring specific permission"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise DRFPermissionDenied(_('Authentication required for this resource.'))

            if not check_user_permission(request.user, permission_name):
                raise DRFPermissionDenied(_('Insufficient permissions for this resource.'))

            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator

def api_verified_user_required(view_func):
    """API decorator requiring verified user"""
    @functools.wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise DRFPermissionDenied(_('Authentication required for this resource.'))

        if not request.user.is_verified:
            raise DRFPermissionDenied(_('Account verification required for this resource.'))

        return view_func(self, request, *args, **kwargs)
    return _wrapped_view

def api_admin_required(view_func):
    """API decorator requiring admin status"""
    @functools.wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise DRFPermissionDenied(_('Authentication required for this resource.'))

        if not request.user.is_staff and not (hasattr(request.user, 'has_role') and
                                             request.user.has_role(RoleChoices.ADMIN)):
            raise DRFPermissionDenied(_('Administrator access required for this resource.'))

        return view_func(self, request, *args, **kwargs)
    return _wrapped_view

# Backward compatibility for existing code
def api_role_required(role_name):
    """Legacy decorator for role-based access"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise DRFPermissionDenied(_('Authentication required for this resource.'))

            if not request.user.is_staff and not (hasattr(request.user, 'has_role') and request.user.has_role(role_name)):
                raise DRFPermissionDenied(_('You do not have the required role to access this resource.'))

            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator

# -------------------------------------------------------------------------
# Performance and Debugging Decorators
# -------------------------------------------------------------------------

def timing_decorator(view_func):
    """Decorator to measure view execution time"""
    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        start_time = time.time()
        result = view_func(request, *args, **kwargs)
        execution_time = time.time() - start_time

        if settings.DEBUG:
            logger.debug(f"View {view_func.__name__} executed in {execution_time:.4f}s")

        return result
    return _wrapped_view

def log_api_calls(view_func):
    """Decorator to log API calls"""
    @functools.wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        if settings.DEBUG:
            log_data = {
                'user': request.user.email if request.user.is_authenticated else 'anonymous',
                'method': request.method,
                'path': request.path,
                'params': dict(request.GET) if request.GET else None,
                'ip': request.META.get('REMOTE_ADDR', ''),
            }

            # Mask sensitive data
            if hasattr(request, 'data') and isinstance(request.data, dict):
                data_copy = request.data.copy()
                for field in ['password', 'token', 'secret', 'credit_card']:
                    if field in data_copy:
                        data_copy[field] = '*****'
                log_data['data'] = data_copy

            logger.debug(f"API Call: {log_data}")

        return view_func(self, request, *args, **kwargs)
    return _wrapped_view

def cache_control(no_cache=False, max_age=None, public=False):
    """Decorator to set cache control headers"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            cache_parts = []

            if no_cache:
                cache_parts.append('no-cache, no-store, must-revalidate')
            elif max_age is not None:
                cache_parts.append(f"max-age={max_age}")

            cache_parts.append('public' if public else 'private')

            if cache_parts:
                response['Cache-Control'] = ', '.join(cache_parts)

            return response
        return _wrapped_view
    return decorator
