import functools
import logging
import time
from typing import Callable, Any, Union, List, Optional
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.conf import settings
from django.core.cache import cache
from functools import wraps
from rest_framework.response import Response
from base.utils import create_response
from rest_framework import status
from django.http import Http404


logger = logging.getLogger(__name__)

# Cache duration constants
CACHE_SHORT = 60  # 1 minute
CACHE_MEDIUM = 300  # 5 minutes
CACHE_LONG = 3600  # 1 hour


def debug_request(view_func: Callable) -> Callable:
    """
    Debug decorator to log request details for troubleshooting.

    Args:
        view_func (Callable): View function to be decorated

    Returns:
        Callable: Wrapped view function with debug logging
    """
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """
        Wrap the view function with debug logging.

        Args:
            request (HttpRequest): Incoming HTTP request
            *args: Positional arguments for the view function
            **kwargs: Keyword arguments for the view function

        Returns:
            Any: Result of the view function
        """
        # Only log in debug mode
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

                # Safely attempt to decode request body
                try:
                    log_data['body'] = request.body.decode('utf-8')
                except Exception:
                    log_data['body'] = 'Unable to decode request body'

                logger.info(f"Debug Request: {log_data}")
            except Exception as e:
                logger.warning(f"Error logging debug request: {e}")

        return view_func(request, *args, **kwargs)
    return wrapper


def handle_exceptions(view_func: Callable) -> Callable:
    """
    Decorator to handle exceptions in view functions.

    Args:
        view_func (Callable): View function to be decorated

    Returns:
        Callable: Wrapped view function with exception handling
    """
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """
        Wrap the view function with global exception handling.

        Args:
            request (HttpRequest): Incoming HTTP request
            *args: Positional arguments for the view function
            **kwargs: Keyword arguments for the view function

        Returns:
            Any: Result of the view function or an error response
        """
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


def has_role(user, role: str) -> bool:
    """
    Centralized role checking function for consistent role verification.

    Args:
        user: User object to check
        role (str): Role name to check for

    Returns:
        bool: Whether the user has the role
    """
    # Check if superuser or staff (always has all roles)
    if user.is_superuser or user.is_staff:
        return True

    # Check using custom role methods
    if hasattr(user, 'has_role') and callable(getattr(user, 'has_role')):
        return user.has_role(role)

    # Check is_admin attribute for admin role
    if role == 'admin' and hasattr(user, 'is_admin') and user.is_admin:
        return True

    # Check role_names list if available
    if hasattr(user, 'role_names'):
        return role in user.role_names

    return False


def role_required(required_roles=None):
    """
    Decorator to check if user has any of the specified roles.
    Uses the accounts app Role model.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Anonymous users don't have roles
            if not request.user.is_authenticated:
                return create_response(
                    error="Authentication required",
                    error_code="not_authenticated",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            # Staff users bypass role checks
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # If no specific roles are required, just require authentication
            if not required_roles:
                return view_func(request, *args, **kwargs)

            # Check if user has any of the required roles
            for role in required_roles:
                if request.user.has_role(role):
                    return view_func(request, *args, **kwargs)

            # No matching roles found
            return create_response(
                error="You don't have permission to perform this action",
                error_code="permission_denied",
                status_code=status.HTTP_403_FORBIDDEN
            )

        return wrapper

    return decorator
def cache_view(timeout: int = 60,
               key_prefix: str = 'view',
               vary_on_user: bool = False):
    """
    Cache view response for improved performance.

    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Prefix for cache key
        vary_on_user (bool): Whether to include user ID in cache key

    Returns:
        Callable: Decorator function for view caching
    """
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Don't cache in debug mode unless explicitly configured
            if settings.DEBUG and not getattr(settings, 'CACHE_IN_DEBUG', False):
                return view_func(request, *args, **kwargs)

            # Don't cache non-GET requests
            if request.method not in ('GET', 'HEAD'):
                return view_func(request, *args, **kwargs)

            # Build cache key
            path = request.get_full_path()
            key_components = [key_prefix, path]

            # Add user ID if vary_on_user is True
            if vary_on_user and request.user.is_authenticated:
                key_components.append(str(request.user.id))

            cache_key = ':'.join(key_components)

            # Try to get cached response
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Call the view function
            response = view_func(request, *args, **kwargs)

            # Cache the response if it's successful
            if hasattr(response, 'status_code') and response.status_code == 200:
                cache.set(cache_key, response, timeout)

            return response
        return wrapper
    return decorator


def timer(logger_obj: Optional[logging.Logger] = None) -> Callable:
    """
    Decorator to measure and log function execution time.

    Args:
        logger_obj (logging.Logger, optional): Custom logger for timing info

    Returns:
        Callable: Decorator function for timing function execution
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        log = logger_obj or logger

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)

                end_time = time.perf_counter()
                execution_time = end_time - start_time

                log.info(
                    f"Function '{func.__name__}' executed in {execution_time:.4f} seconds"
                )

                return result

            except Exception as e:
                end_time = time.perf_counter()
                execution_time = end_time - start_time

                log.error(
                    f"Function '{func.__name__}' failed after {execution_time:.4f} seconds: {e}"
                )

                raise
        return wrapper
    return decorator


def validate_params(**param_types: Any):
    """
    Decorator to validate function parameters based on type hints.

    Args:
        **param_types: Mapping of parameter names to their expected types

    Returns:
        Callable: Decorator function for parameter validation

    Raises:
        TypeError: If parameter types do not match expectations
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Validate positional arguments
            for i, (arg_name, expected_type) in enumerate(param_types.items()):
                if i < len(args):
                    if not isinstance(args[i], expected_type):
                        raise TypeError(
                            f"Argument '{arg_name}' must be of type {expected_type}, "
                            f"got {type(args[i])}"
                        )

            # Validate keyword arguments
            for arg_name, arg_value in kwargs.items():
                if arg_name in param_types:
                    expected_type = param_types[arg_name]
                    if not isinstance(arg_value, expected_type):
                        raise TypeError(
                            f"Argument '{arg_name}' must be of type {expected_type}, "
                            f"got {type(arg_value)}"
                        )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def retry(max_attempts: int = 3,
          exceptions: Union[Exception, tuple] = Exception,
          delay: float = 1.0):
    """
    Decorator to retry a function in case of specified exceptions.

    Args:
        max_attempts (int): Maximum number of retry attempts
        exceptions (Exception or tuple): Exception types to catch and retry
        delay (float): Delay between retry attempts in seconds

    Returns:
        Callable: Decorator function for retry mechanism
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(
                            f"Function '{func.__name__}' failed after {max_attempts} attempts. "
                            f"Last error: {e}"
                        )
                        raise

                    logger.warning(
                        f"Attempt {attempts} failed for '{func.__name__}': {e}. Retrying..."
                    )
                    time.sleep(delay)

            raise RuntimeError("Retry mechanism failed unexpectedly")
        return wrapper
    return decorator


def audit_log(log_input: bool = True, log_output: bool = True):
    """
    Decorator to log function inputs and outputs for auditing purposes.

    Args:
        log_input (bool): Whether to log input parameters
        log_output (bool): Whether to log return value

    Returns:
        Callable: Decorator function for audit logging
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Log input if enabled
            if log_input:
                # Sanitize sensitive data from logs
                sanitized_kwargs = {
                    k: '******' if k.lower() in ('password', 'token', 'key', 'secret') else v
                    for k, v in kwargs.items()
                }

                logger.info(
                    f"Audit Log - Input to {func.__name__}: "
                    f"args={args}, kwargs={sanitized_kwargs}"
                )

            try:
                result = func(*args, **kwargs)

                # Log output if enabled
                if log_output:
                    # Avoid logging large responses
                    if hasattr(result, '__len__') and len(result) > 1000:
                        logger.info(
                            f"Audit Log - Output from {func.__name__}: "
                            f"[Large response of type {type(result).__name__}]"
                        )
                    else:
                        logger.info(
                            f"Audit Log - Output from {func.__name__}: "
                            f"result={result}"
                        )

                return result

            except Exception as e:
                logger.error(
                    f"Audit Log - Exception in {func.__name__}: {e}"
                )
                raise
        return wrapper
    return decorator


def with_cache(cache_key_prefix: str, timeout: int = CACHE_MEDIUM):
    """
    Decorator to cache DRF view results with dynamic cache key generation.

    Args:
        cache_key_prefix (str): Prefix for the cache key
        timeout (int): Cache timeout in seconds

    Returns:
        Callable: Decorator function for view caching

    Example:
        @with_cache('list_auctions')
        def list_auctions(request):
            # Implementation without manual cache handling
            return Response(data)
    """
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Skip caching for non-GET requests
            if request.method not in ('GET', 'HEAD'):
                return view_func(request, *args, **kwargs)

            # Generate cache key based on request params
            cache_key = f"{cache_key_prefix}_{hash(frozenset(request.query_params.items()))}"

            # Try to get cached response
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                from rest_framework.response import Response
                return Response(cached_data)

            # Call the view function
            response = view_func(request, *args, **kwargs)

            # Cache the response data if it's a Response object with data
            if hasattr(response, 'data'):
                cache.set(cache_key, response.data, timeout)

            return response
        return wrapper
    return decorator




def arabic_slugify(text):
    """
    Custom slugify function that preserves Arabic characters.
    Replaces spaces and special characters with hyphens.

    Args:
        text (str): The text to slugify

    Returns:
        str: Arabic-friendly slug
    """
    if not text:
        return ""

    # Keep Arabic and Latin letters, numbers
    text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\w\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text).strip('-')
    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)
    return text

@timer()
def find_by_slug_or_id(model_class, slug_or_id, raise_404=True):
    """
    Utility function to find an object by slug or ID.
    Useful when you want to support both slug and ID-based lookups.

    Args:
        model_class: Django model class to query
        slug_or_id (str): Slug or ID to look up
        raise_404 (bool): Whether to raise 404 if not found

    Returns:
        Model instance or None
    """
    # Try to find by slug first
    try:
        return model_class.objects.get(slug=slug_or_id)
    except model_class.DoesNotExist:
        # If slug lookup fails, try ID lookup if it looks like an ID
        if slug_or_id.isdigit():
            try:
                return model_class.objects.get(id=int(slug_or_id))
            except model_class.DoesNotExist:
                pass

    # If we get here, object wasn't found
    if raise_404:
        raise Http404(f"{model_class.__name__} not found with slug or ID '{slug_or_id}'")
    return None

def cache_slug_lookup(timeout=300):
    """
    Decorator for caching slug lookups.
    Caches the result of finding objects by slug.

    Args:
        timeout (int): Cache timeout in seconds

    Returns:
        Decorator function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, slug=None, *args, **kwargs):
            if not slug:
                return view_func(self, request, slug=slug, *args, **kwargs)

            # Generate cache key
            model_name = self.queryset.model.__name__.lower()
            cache_key = f"slug_lookup:{model_name}:{slug}"

            # Try to get from cache
            cached_id = cache.get(cache_key)
            if cached_id:
                try:
                    obj = self.queryset.model.objects.get(id=cached_id)
                    # Set in kwargs and continue with view
                    kwargs['object'] = obj
                    logger.debug(f"Slug cache hit for {model_name}:{slug}")
                    return view_func(self, request, slug=slug, *args, **kwargs)
                except self.queryset.model.DoesNotExist:
                    # Object was deleted, remove from cache
                    cache.delete(cache_key)

            # Cache miss, look up object and cache its ID
            response = view_func(self, request, slug=slug, *args, **kwargs)

            # If response is successful, try to cache the slug->id mapping
            if hasattr(response, 'status_code') and response.status_code == 200:
                try:
                    # Extract object ID from the response data
                    if hasattr(response, 'data') and 'id' in response.data:
                        obj_id = response.data['id']
                        cache.set(cache_key, obj_id, timeout)
                        logger.debug(f"Cached slug mapping {model_name}:{slug}->{obj_id}")
                except Exception as e:
                    logger.warning(f"Failed to cache slug mapping: {e}")

            return response
        return wrapper
    return decorator

# Function to help build more efficient URLs
def get_absolute_url_by_slug(obj):
    """
    Get the absolute URL for an object using its slug.

    Args:
        obj: Django model instance with a slug field

    Returns:
        str: Absolute URL
    """
    model_name = obj.__class__.__name__.lower()

    if hasattr(obj, 'slug') and obj.slug:
        return f"/api/{model_name}s/by-slug/{obj.slug}/"

    # Fallback to ID-based URL
    return f"/api/{model_name}s/{obj.id}/"
