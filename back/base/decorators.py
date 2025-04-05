import functools
import logging
import time
from typing import Callable, Any, Optional
from django.http import HttpRequest
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

# Cache durations in seconds
CACHE_SHORT = 60    # 1 minute
CACHE_MEDIUM = 300  # 5 minutes
CACHE_LONG = 3600   # 1 hour

def debug_request(view_func: Callable) -> Callable:
    """Log request details for debugging"""
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        if settings.DEBUG:
            try:
                log_data = {
                    'method': request.method,
                    'path': request.path,
                    'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                    'query_params': dict(request.GET),
                    'headers': {k: v for k, v in request.headers.items()
                               if k.lower() not in ['cookie', 'authorization']}
                }
                logger.info(f"Debug Request: {log_data}")
            except Exception as e:
                logger.warning(f"Error logging debug request: {e}")
        return view_func(request, *args, **kwargs)
    return wrapper

def handle_exceptions(view_func: Callable) -> Callable:
    """Handle common exceptions in views"""
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        try:
            return view_func(request, *args, **kwargs)
        except PermissionDenied as e:
            logger.warning(f"Permission denied: {e}")
            return Response({
                'error': str(e),
                'error_code': 'permission_denied'
            }, status=403)
        except Exception as e:
            logger.error(f"Unhandled exception in {view_func.__name__}: {e}", exc_info=True)
            return Response({
                'error': 'An unexpected error occurred',
                'error_code': 'unexpected_error'
            }, status=500)
    return wrapper

def cache_view(timeout: int = CACHE_MEDIUM, key_prefix: str = 'view', vary_on_user: bool = False):
    """Cache view responses for improved performance"""
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Skip cache in debug mode or for non-GET requests
            if (settings.DEBUG and not getattr(settings, 'CACHE_IN_DEBUG', False) or
                request.method not in ('GET', 'HEAD')):
                return view_func(request, *args, **kwargs)

            # Build cache key
            path = request.get_full_path()
            key_components = [key_prefix, path]
            if vary_on_user and request.user.is_authenticated:
                key_components.append(str(request.user.id))
            cache_key = ':'.join(key_components)

            # Try cached response first
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Generate and cache the response
            response = view_func(request, *args, **kwargs)
            if hasattr(response, 'status_code') and response.status_code == 200:
                cache.set(cache_key, response, timeout)
            return response
        return wrapper
    return decorator

def role_required(required_roles=None):
    """Decorator to check if user has any of the specified roles"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Handle authentication and permissions
            if not request.user.is_authenticated:
                return Response(
                    {"error": "Authentication required", "error_code": "not_authenticated"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Staff users bypass role checks
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # No specific roles required, just authentication
            if not required_roles:
                return view_func(request, *args, **kwargs)

            # Check for any required role
            for role in required_roles:
                if request.user.has_role(role):
                    return view_func(request, *args, **kwargs)

            return Response(
                {"error": "You don't have permission to perform this action",
                 "error_code": "permission_denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        return wrapper
    return decorator

def timer(logger_obj: Optional[logging.Logger] = None):
    """Measure and log function execution time"""
    def decorator(func: Callable):
        log = logger_obj or logger

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                log.info(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                log.error(f"Function '{func.__name__}' failed after {execution_time:.4f} seconds: {e}")
                raise
        return wrapper
    return decorator
