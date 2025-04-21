# Path: accounts/middleware.py
import json
import logging
import time
import re
import asyncio
# from django.utils.deprecation import MiddlewareMixin # Not needed for new style middleware
from django.conf import settings
from .utils import send_login_alert_email # Assuming this exists
# from inspect import iscoroutinefunction # Use asyncio.iscoroutinefunction instead
from django.utils import timezone  # Add this import at the top

logger = logging.getLogger(__name__)

# --- Request Logging Middleware ---
class RequestLogMiddleware:
    """
    Middleware to log API requests and responses, calculate duration,
    and handle both sync and async requests.
    """
    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self.is_async = asyncio.iscoroutinefunction(self.get_response)
        self.excluded_paths = [re.compile(p) for p in getattr(settings, 'LOGGING_EXCLUDED_PATHS', [
            r'^/admin/',
            r'^/static/',
            r'^/media/',
            r'^/favicon\.ico$'
        ])] # Make excluded paths configurable via settings

    def is_excluded_path(self, path):
        """Check if the path should be excluded from logging"""
        return any(pattern.match(path) for pattern in self.excluded_paths)

    def _log_request(self, request):
        """Helper to log request details."""
        if self.is_excluded_path(request.path_info):
            return

        request.req_start_time = time.monotonic() # Use monotonic clock for duration

        if settings.DEBUG:
            meta = {k: v for k, v in request.META.items() if k.startswith(('HTTP_', 'REMOTE_', 'REQUEST_', 'CONTENT_', 'SERVER_'))}
            # Redact sensitive headers
            for k in ['HTTP_COOKIE', 'HTTP_AUTHORIZATION', 'HTTP_X_CSRFTOKEN']:
                if k in meta:
                    meta[k] = '[REDACTED]'

            logger.debug(f"REQUEST START: {request.method} {request.path_info} from {meta.get('REMOTE_ADDR')}")
            # logger.debug(f"REQUEST META: {meta}") # Optional: Log full meta if needed

            # Log request body (masking passwords)
            if request.method not in ['GET', 'HEAD', 'OPTIONS'] and hasattr(request, 'body'):
                try:
                    body = request.body.decode('utf-8', errors='replace') # Handle potential decode errors
                    if body:
                        content_type = request.META.get('CONTENT_TYPE', '').lower()
                        if 'application/json' in content_type:
                            try:
                                body_data = json.loads(body)
                                masked_data = self._mask_sensitive_data(body_data)
                                logger.debug(f"REQUEST BODY (JSON): {json.dumps(masked_data)}")
                            except json.JSONDecodeError:
                                logger.debug(f"REQUEST BODY (Invalid JSON): {body[:500]}") # Log truncated raw body
                        elif 'application/x-www-form-urlencoded' in content_type:
                             # Handled by FormSubmissionLoggingMiddleware if enabled
                             pass
                             # Or log here if that middleware is not used:
                             # from django.http import QueryDict
                             # masked_data = self._mask_sensitive_data(QueryDict(body).dict())
                             # logger.debug(f"REQUEST BODY (Form): {masked_data}")
                        else:
                            # Log truncated generic body
                             log_body = body if len(body) <= 1000 else f"{body[:1000]}... [truncated]"
                             logger.debug(f"REQUEST BODY (Other): {log_body}")

                except Exception as e: # Catch broader errors during body logging
                     logger.warning(f"Could not log request body for {request.path_info}: {e}")


    def _log_response(self, request, response):
        """Helper to log response details."""
        if self.is_excluded_path(request.path_info) or not hasattr(request, 'req_start_time'):
             return response # Don't log excluded or if start time is missing

        duration = time.monotonic() - request.req_start_time
        duration_ms = round(duration * 1000)

        # Add duration header
        response['X-Request-Duration-Ms'] = str(duration_ms)

        status_code = getattr(response, 'status_code', 0)

        # Log summary line
        log_level = logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR
        logger.log(log_level, f"RESPONSE: {request.method} {request.path_info} - Status {status_code} in {duration_ms}ms")


        # Log slow requests
        slow_request_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 1000)
        if duration_ms > slow_request_threshold:
            logger.warning(
                f"SLOW REQUEST: {request.method} {request.path_info} took {duration:.3f}s"
            )

        # Log response body in debug mode for JSON
        if settings.DEBUG:
            content_type = response.get('Content-Type', '').lower()
            if 'application/json' in content_type and hasattr(response, 'content'):
                try:
                    content = response.content.decode('utf-8', errors='replace')
                    log_content = content if len(content) <= 1000 else f"{content[:1000]}... [truncated]"
                    # Consider masking response data too if sensitive
                    logger.debug(f"RESPONSE CONTENT: {log_content}")
                except Exception as e:
                     logger.warning(f"Could not log response content for {request.path_info}: {e}")

        return response

    def _mask_sensitive_data(self, data):
        """Utility to mask sensitive data in logs (used by request logging)."""
        # Simplified version, reuse the one from FormSubmissionLoggingMiddleware if needed
        if isinstance(data, dict):
            masked_data = {}
            for k, v in data.items():
                if any(keyword in k.lower() for keyword in ['password', 'token', 'secret', 'authorization', 'cookie']):
                    masked_data[k] = '[REDACTED]'
                elif isinstance(v, dict):
                     masked_data[k] = self._mask_sensitive_data(v) # Recurse
                elif isinstance(v, list):
                     # Basic list handling, doesn't recurse into list items deeply
                     masked_data[k] = '[LIST]' if any(keyword in k.lower() for keyword in ['password', 'token', 'secret']) else v
                else:
                    masked_data[k] = v
            return masked_data
        return data # Return non-dict data as is


    async def __call__(self, request):
        # Process request before the view
        self._log_request(request)

        # Call the next middleware/view
        response = await self.get_response(request) if self.is_async else self.get_response(request)

        # Await response if it's a coroutine (can happen with mixed sync/async middleware)
        if asyncio.iscoroutine(response):
             response = await response

        # Process response after the view
        return self._log_response(request, response)

# Alias for backward compatibility if needed in settings.py
class RequestResponseLoggingMiddleware(RequestLogMiddleware):
    pass

# --- Login Tracking Middleware ---
class LoginTrackingMiddleware:
    """
    Middleware to extract client IP and User-Agent for login attempts.
    Relies on the login view calling `track_successful_login`.
    """
    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self.is_async = asyncio.iscoroutinefunction(self.get_response)
        # Consider making login path configurable via settings
        self.login_path_pattern = re.compile(getattr(settings, 'LOGIN_PATH_REGEX', r'/api/v1/auth/login/?$')) # Example path

    def _get_client_ip(self, request):
        """Extract the client IP address, respecting X-Forwarded-For."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        # Basic validation (optional)
        # try:
        #     ipaddress.ip_address(ip)
        # except ValueError:
        #     ip = None # Or a default placeholder
        return ip if ip else '0.0.0.0' # Return a default if IP is somehow missing


    def _process_request(self, request):
        """Attach client info to request if it matches the login path."""
        # Use regex matching for flexibility
        if self.login_path_pattern.search(request.path_info) and request.method == 'POST':
            try:
                request.client_ip = self._get_client_ip(request)
                request.user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            except Exception as e:
                 logger.error(f"Error in LoginTrackingMiddleware setting request attributes: {str(e)}", exc_info=True)
        # else:
        #     # Ensure attributes don't exist on non-login requests if needed
        #     request.client_ip = None
        #     request.user_agent = None


    async def __call__(self, request):
        # Process request to potentially add client info
        self._process_request(request)

        # Call the next middleware/view
        response = await self.get_response(request) if self.is_async else self.get_response(request)

        # Await response if it's a coroutine
        if asyncio.iscoroutine(response):
            response = await response

        # No response processing needed for this middleware
        return response


# --- Form Submission Logging Middleware ---
class FormSubmissionLoggingMiddleware:
    """
    Middleware to log form submissions (POST/PUT/PATCH data) in DEBUG mode, masking sensitive fields.
    Handles JSON, form-urlencoded, and DRF request.data.
    """
    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self.is_async = asyncio.iscoroutinefunction(self.get_response)
        # Define sensitive fields (make configurable via settings?)
        self.sensitive_fields = getattr(settings, 'LOGGING_SENSITIVE_FIELDS', [
            'password', 'password1', 'password2', 'new_password',
            'old_password', 'confirm_password', 'verification_code',
            'reset_code', 'secret', 'token', 'api_key', 'credit_card',
            'card_number', 'cvv', 'ssn', 'authorization', 'cookie' # Added auth/cookie
        ])

    def _mask_sensitive_data(self, data):
        """Mask sensitive data recursively in dictionaries."""
        if not isinstance(data, dict):
            return data # Return non-dict data as is

        masked_data = {}
        for key, value in data.items():
            # Check if the key itself indicates sensitivity
            key_lower = key.lower()
            is_sensitive = any(sf in key_lower for sf in self.sensitive_fields)

            if is_sensitive:
                masked_data[key] = '********'
            elif isinstance(value, dict):
                # Recurse for nested dictionaries
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                # Recurse for items in lists if they are dicts
                 masked_data[key] = [self._mask_sensitive_data(item) if isinstance(item, dict) else item for item in value]
            else:
                 # Keep non-dict, non-list, non-sensitive values
                masked_data[key] = value
        return masked_data

    def _process_request(self, request):
        """Log form/data submissions if conditions met."""
        if not settings.DEBUG:
            return

        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']: # Include DELETE?
            return

        content_type = request.META.get('CONTENT_TYPE', '').lower()

        # Skip large multipart uploads
        if 'multipart/form-data' in content_type:
            logger.debug(f"[FormLogging] Skipping multipart form data for {request.method} {request.path_info}")
            return

        log_data = None
        log_source = "Unknown"

        try:
             # Check DRF's request.data first if available (handles JSON, form data parsed by DRF)
            if hasattr(request, 'data') and request.data:
                 log_data = request.data
                 log_source = "request.data"
            # Fallback to request.POST (for standard Django forms)
            elif request.POST:
                log_data = request.POST.dict() # Convert QueryDict to dict
                log_source = "request.POST"
            # Fallback to parsing raw body for JSON if request.data wasn't available/used
            elif 'application/json' in content_type and hasattr(request, 'body') and request.body:
                 try:
                     log_data = json.loads(request.body)
                     log_source = "request.body (JSON)"
                 except json.JSONDecodeError:
                     logger.debug(f"[FormLogging] Invalid JSON body for {request.method} {request.path_info}")
                     return # Don't log if JSON is invalid

            # If we have data to log, mask and log it
            if log_data:
                masked_data = self._mask_sensitive_data(log_data)
                # Convert to JSON string for consistent logging format
                try:
                     log_str = json.dumps(masked_data, ensure_ascii=False, default=str) # Use default=str for non-serializable types
                except TypeError:
                     log_str = str(masked_data) # Fallback to string representation

                # Truncate very large logs
                if len(log_str) > 2000:
                    log_str = f"{log_str[:2000]}... [truncated]"

                logger.debug(f"[FormLogging] Data ({log_source}) for {request.method} {request.path_info}: {log_str}")

        except Exception as e:
            logger.warning(f"[FormLogging] Could not log submission data for {request.method} {request.path_info}: {e}", exc_info=True)


    async def __call__(self, request):
        # Process request for form logging
        self._process_request(request)

        # Call the next middleware/view
        response = await self.get_response(request) if self.is_async else self.get_response(request)

        # Await response if it's a coroutine
        if asyncio.iscoroutine(response):
            response = await response

        # No response processing needed
        return response


# --- Login Tracking Helper Function ---
# To be called explicitly from your login view upon successful authentication
def track_successful_login(user, request):
    """
    Tracks successful login, logs info, and sends alerts for potentially new devices/locations.

    Args:
        user: The authenticated CustomUser object.
        request: The Django request object (should have client_ip and user_agent attached by middleware).
    """
    try:
        # Get IP and user agent from request (attached by LoginTrackingMiddleware)
        ip_address = getattr(request, 'client_ip', request.META.get('REMOTE_ADDR', '0.0.0.0'))
        user_agent = getattr(request, 'user_agent', request.META.get('HTTP_USER_AGENT', 'Unknown'))

        # --- Suspicious Activity Detection Logic ---
        # TODO: Implement actual logic to check if this device/location is new or suspicious for this user.
        # This requires storing historical login data (IP, User-Agent, Timestamp) per user.
        # Example placeholder:
        # known_devices = UserLoginHistory.objects.filter(user=user).values_list('ip_address', 'user_agent')
        # is_new_ip = ip_address not in [d[0] for d in known_devices]
        # is_new_ua = user_agent not in [d[1] for d in known_devices]
        # is_new_device = is_new_ip or is_new_ua # Simple example
        is_new_device = True # <<< Placeholder - Replace with real check!

        # Log the successful login attempt details
        logger.info(f"Successful login for {user.email}. IP: {ip_address}, User-Agent: '{user_agent}'. New device/location: {is_new_device}")

        # --- Store Login History ---
        # TODO: Save this login attempt to a database model (e.g., UserLoginHistory)
        # UserLoginHistory.objects.create(user=user, ip_address=ip_address, user_agent=user_agent)

        # --- Send Alert for New Device/Location ---
        if is_new_device:
             logger.warning(f"Potentially new device/location detected for user {user.email} from IP {ip_address}")
             # Send alert email (use async task runner like Celery in production)
             if not settings.DEBUG: # Avoid sending emails in debug mode unless configured
                try:
                     # TODO: Implement IP geolocation lookup for location info
                     location_info = "Unknown Location" # Placeholder
                     # Consider running this in a background task
                     send_login_alert_email(
                        recipient_email=user.email,
                        ip_address=ip_address,
                        device_info=user_agent,
                        location=location_info,
                        login_time=timezone.now() # Pass current time
                     )
                     logger.info(f"Login alert email sent to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send login alert email to {user.email}: {str(e)}", exc_info=True)


    except Exception as e:
        logger.error(f"Error during track_successful_login for user {getattr(user, 'email', 'N/A')}: {str(e)}", exc_info=True)
        # Do not interrupt the login process, just log the tracking error.
