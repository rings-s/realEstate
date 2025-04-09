import functools
import time
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from accounts.models import Role
from .utils import check_user_permission, check_auction_status


# -------------------------------------------------------------------------
# View Decorators
# -------------------------------------------------------------------------

def role_required(role_name):
    """
    Decorator to require a specific role for accessing a view.

    Args:
        role_name (str): Role name required for access

    Returns:
        function: Decorated view function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': _('يرجى تسجيل الدخول للوصول إلى هذه الصفحة.')}, status=403)
                return redirect(settings.LOGIN_URL)

            # Check if user has the required role
            if not request.user.has_role(role_name):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': _('ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة.')}, status=403)
                raise PermissionDenied(_('ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة.'))

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def verified_user_required(view_func):
    """
    Decorator to require a verified user for accessing a view.

    Args:
        view_func: View function to decorate

    Returns:
        function: Decorated view function
    """
    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': _('يرجى تسجيل الدخول للوصول إلى هذه الصفحة.')}, status=403)
            return redirect(settings.LOGIN_URL)

        # Check if user is verified
        if not request.user.is_verified:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': _('يجب توثيق حسابك للوصول إلى هذه الصفحة.')}, status=403)
            return redirect('accounts:verification_required')

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def permission_required(permission_name):
    """
    Decorator to require a specific permission for accessing a view.

    Args:
        permission_name (str): Permission name required for access

    Returns:
        function: Decorated view function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': _('يرجى تسجيل الدخول للوصول إلى هذه الصفحة.')}, status=403)
                return redirect(settings.LOGIN_URL)

            # Check if user has the required permission
            if not check_user_permission(request.user, permission_name):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': _('ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة.')}, status=403)
                raise PermissionDenied(_('ليس لديك صلاحيات كافية للوصول إلى هذه الصفحة.'))

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def property_owner_required(model=None, pk_url_kwarg='pk'):
    """
    Decorator to require property ownership for accessing a view.

    Args:
        model: Model class to use for lookup (if None, will be determined from view)
        pk_url_kwarg (str): URL kwarg containing the primary key

    Returns:
        function: Decorated view function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': _('يرجى تسجيل الدخول للوصول إلى هذه الصفحة.')}, status=403)
                return redirect(settings.LOGIN_URL)

            # Admin users bypass this check
            if request.user.has_role(Role.ADMIN):
                return view_func(request, *args, **kwargs)

            # Get the primary key from URL kwargs
            pk = kwargs.get(pk_url_kwarg)
            if not pk:
                raise Http404(_('لم يتم توفير معرف العقار.'))

            # Determine the model class
            model_class = model
            if model_class is None:
                # Try to get model from view
                if hasattr(view_func, 'view_class'):
                    model_class = view_func.view_class.model
                if model_class is None:
                    # Default to Property model
                    from .models import Property
                    model_class = Property

            # Get the object
            try:
                obj = model_class.objects.get(pk=pk)
            except model_class.DoesNotExist:
                raise Http404(_('العقار غير موجود.'))

            # Check owner field name (default is 'owner')
            owner_field = 'owner'
            if not hasattr(obj, owner_field):
                owner_field = 'user'  # Alternative owner field

            # Check if user is the owner
            owner = getattr(obj, owner_field, None)
            if owner != request.user:
                # Check if user is an agent for the owner (if applicable)
                is_agent = False
                if request.user.has_role(Role.AGENT):
                    # This implementation assumes a relationship model between agents and sellers
                    # You would need to implement this based on your specific data model
                    # Example: is_agent = AgentClientRelationship.objects.filter(agent=request.user, client=owner).exists()
                    pass

                if not is_agent:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': _('يمكن الوصول إلى هذا العقار فقط من قِبل المالك أو الوكيل المفوض.')}, status=403)
                    raise PermissionDenied(_('يمكن الوصول إلى هذا العقار فقط من قِبل المالك أو الوكيل المفوض.'))

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def auction_status_required(statuses, redirect_url=None):
    """
    Decorator to require specific auction status for accessing a view.

    Args:
        statuses (list): List of required auction statuses
        redirect_url (str): URL to redirect if status check fails

    Returns:
        function: Decorated view function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get auction ID from URL kwargs
            auction_id = kwargs.get('auction_id') or kwargs.get('pk')
            if not auction_id:
                return view_func(request, *args, **kwargs)  # Skip check if no auction ID

            # Get auction
            from .models import Auction
            try:
                auction = Auction.objects.get(pk=auction_id)
            except Auction.DoesNotExist:
                raise Http404(_('المزاد غير موجود.'))

            # Update auction status if needed
            current_status = check_auction_status(auction)

            # Check if current status is in required statuses
            if current_status not in statuses:
                error_msg = _('لا يمكن الوصول إلى هذا المزاد في حالته الحالية.')

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

def api_role_required(role_name):
    """
    Decorator to require a specific role for accessing an API view.

    Args:
        role_name (str): Role name required for access

    Returns:
        function: Decorated view function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                raise DRFPermissionDenied(_('يرجى تسجيل الدخول للوصول إلى هذا المورد.'))

            # Check if user has the required role
            if not request.user.has_role(role_name):
                raise DRFPermissionDenied(_('ليس لديك صلاحيات كافية للوصول إلى هذا المورد.'))

            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator


def api_verified_user_required(view_func):
    """
    Decorator to require a verified user for accessing an API view.

    Args:
        view_func: View function to decorate

    Returns:
        function: Decorated view function
    """
    @functools.wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            raise DRFPermissionDenied(_('يرجى تسجيل الدخول للوصول إلى هذا المورد.'))

        # Check if user is verified
        if not request.user.is_verified:
            raise DRFPermissionDenied(_('يجب توثيق حسابك للوصول إلى هذا المورد.'))

        return view_func(self, request, *args, **kwargs)
    return _wrapped_view


def api_permission_required(permission_name):
    """
    Decorator to require a specific permission for accessing an API view.

    Args:
        permission_name (str): Permission name required for access

    Returns:
        function: Decorated view function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                raise DRFPermissionDenied(_('يرجى تسجيل الدخول للوصول إلى هذا المورد.'))

            # Check if user has the required permission
            if not check_user_permission(request.user, permission_name):
                raise DRFPermissionDenied(_('ليس لديك صلاحيات كافية للوصول إلى هذا المورد.'))

            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator


# -------------------------------------------------------------------------
# Performance and Debugging Decorators
# -------------------------------------------------------------------------

def timing_decorator(view_func):
    """
    Decorator to time a view function execution.

    Args:
        view_func: View function to decorate

    Returns:
        function: Decorated view function
    """
    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        start_time = time.time()
        result = view_func(request, *args, **kwargs)
        execution_time = time.time() - start_time

        # Log execution time (modify as needed)
        if settings.DEBUG:
            print(f"View {view_func.__name__} took {execution_time:.4f} seconds to execute.")

        return result
    return _wrapped_view


def log_api_calls(view_func):
    """
    Decorator to log API calls for debugging.

    Args:
        view_func: View function to decorate

    Returns:
        function: Decorated view function
    """
    @functools.wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger('api_calls')

        # Log request information
        log_data = {
            'user': request.user.email if request.user.is_authenticated else 'anonymous',
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'data': request.data if hasattr(request, 'data') else {},
            'ip': request.META.get('REMOTE_ADDR', ''),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # Log sensitive fields with asterisks
        sensitive_fields = ['password', 'token', 'credit_card', 'access_code']
        if isinstance(log_data['data'], dict):
            for field in sensitive_fields:
                if field in log_data['data']:
                    log_data['data'][field] = '*****'

        logger.info(f"API Call: {log_data}")

        # Execute the view
        return view_func(self, request, *args, **kwargs)
    return _wrapped_view


def cache_control(no_cache=False, max_age=None, public=False):
    """
    Decorator to set cache control headers.

    Args:
        no_cache (bool): Set no-cache directive
        max_age (int): Cache max-age in seconds
        public (bool): Set public directive

    Returns:
        function: Decorated view function
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)

            # Set Cache-Control header
            cache_control_parts = []

            if no_cache:
                cache_control_parts.append('no-cache, no-store, must-revalidate')
            elif max_age is not None:
                cache_control_parts.append(f"max-age={max_age}")

            if public:
                cache_control_parts.append('public')
            else:
                cache_control_parts.append('private')

            if cache_control_parts:
                response['Cache-Control'] = ', '.join(cache_control_parts)

            return response
        return _wrapped_view
    return decorator
