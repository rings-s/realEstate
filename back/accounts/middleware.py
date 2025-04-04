# Path: accounts/middleware.py
# This file contains middleware for request logging, login tracking, and form submission logging
# These middlewares support both synchronous and asynchronous requests

import json
import logging
import time
import re
import inspect
import asyncio
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .utils import send_login_alert_email

logger = logging.getLogger(__name__)


class RequestLogMiddleware:
    """
    Middleware to log API requests and responses
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Define paths that should not be logged (e.g., static files)
        self.excluded_paths = [
            r'^/admin/',
            r'^/static/',
            r'^/media/',
            r'^/favicon\.ico$'
        ]
        # Check if get_response is async
        self.is_async = asyncio.iscoroutinefunction(get_response)

    def is_excluded_path(self, path):
        """Check if the path should be excluded from logging"""
        return any(re.match(pattern, path) for pattern in self.excluded_paths)

    def process_request(self, request):
        """Process request before view is called"""
        # Skip excluded paths
        if self.is_excluded_path(request.path):
            return None

        # Add request timestamp for performance tracking
        request.req_start_time = time.time()

        # Log request details in debug mode
        if settings.DEBUG:
            meta = request.META.copy()
            # Remove sensitive info
            for k in ['HTTP_COOKIE', 'HTTP_AUTHORIZATION']:
                if k in meta:
                    meta[k] = '[REDACTED]'

            logger.debug(f"REQUEST: {request.method} {request.path} from {meta.get('REMOTE_ADDR')}")

            # Log request body for non-GET methods
            if request.method not in ['GET', 'HEAD'] and hasattr(request, 'body'):
                try:
                    body = request.body.decode('utf-8')
                    if body:
                        # Try to parse as JSON
                        try:
                            body_data = json.loads(body)
                            # Mask password fields
                            if isinstance(body_data, dict):
                                for key in body_data:
                                    if 'password' in key.lower():
                                        body_data[key] = '[REDACTED]'
                            logger.debug(f"REQUEST BODY: {json.dumps(body_data)}")
                        except json.JSONDecodeError:
                            # Not JSON, log as raw (may be form data)
                            if len(body) > 1000:
                                logger.debug(f"REQUEST BODY: {body[:1000]}... [truncated]")
                            else:
                                logger.debug(f"REQUEST BODY: {body}")
                except UnicodeDecodeError:
                    logger.debug("REQUEST BODY: [Binary data]")

        return None

    def process_response(self, request, response):
        """Process response after view is called"""
        # Skip excluded paths
        if self.is_excluded_path(request.path):
            return response

        # Calculate request duration
        if hasattr(request, 'req_start_time'):
            duration = time.time() - request.req_start_time
            response['X-Request-Duration'] = str(round(duration * 1000)) + 'ms'

            # Log slow requests
            if duration > 1.0:  # Requests taking more than 1 second
                logger.warning(
                    f"SLOW REQUEST: {request.method} {request.path} took {duration:.2f}s"
                )

        # Log response in debug mode
        if settings.DEBUG:
            status_code = getattr(response, 'status_code', 0)
            logger.debug(f"RESPONSE: {request.method} {request.path} - {status_code}")

            # Log response content for API responses
            if (hasattr(response, 'content') and
                'application/json' in response.get('Content-Type', '')):
                try:
                    content = response.content.decode('utf-8')
                    if len(content) > 1000:
                        logger.debug(f"RESPONSE CONTENT: {content[:1000]}... [truncated]")
                    else:
                        logger.debug(f"RESPONSE CONTENT: {content}")
                except:
                    pass

        return response

    # This is the corrected version of the RequestLogMiddleware.__call__ method

    async def __call__(self, request):
        """Handle both sync and async calls"""
        # Process request
        response = self.process_request(request)
        if response is not None:
            return response
        
        # Get response from the next middleware/view
        if self.is_async:
            response = await self.get_response(request)
        else:
            response = self.get_response(request)
            
        # If response is a coroutine, await it
        if asyncio.iscoroutine(response):
            response = await response
            
        # Process response
        return self.process_response(request, response)

# Add this class to maintain compatibility with settings.py
class RequestResponseLoggingMiddleware(RequestLogMiddleware):
    """
    Alias for RequestLogMiddleware to maintain compatibility with existing settings
    """
    pass


class LoginTrackingMiddleware:
    """
    Middleware to track user logins and detect potential suspicious activity
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Check if get_response is async
        self.is_async = asyncio.iscoroutinefunction(get_response)

    def process_request(self, request):
        """Process each request to check for login attempts"""
        # Only check login endpoints
        if request.path.endswith('/login/') and request.method == 'POST':
            try:
                # Get IP and user agent
                ip_address = self._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

                # Check if this is a successful login (happens in the view)
                # We'll add a hook in the login view to call a tracking function

                # For now, just set the IP and user agent on the request
                request.client_ip = ip_address
                request.user_agent = user_agent

            except Exception as e:
                logger.error(f"Error in LoginTrackingMiddleware: {str(e)}")

        return None

    def _get_client_ip(self, request):
        """Extract the client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For header contains proxy chain, first item is client IP
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip

    async def __call__(self, request):
        """Handle both sync and async calls"""
        # Process request
        response = self.process_request(request)
        if response is not None:
            return response
        
        # Get response from the next middleware/view
        if self.is_async:
            response = await self.get_response(request)
        else:
            response = self.get_response(request)
            
        # If response is a coroutine, await it
        if asyncio.iscoroutine(response):
            response = await response
            
        return response


class FormSubmissionLoggingMiddleware:
    """
    Middleware to log form submissions in debug mode
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Check if get_response is async
        self.is_async = asyncio.iscoroutinefunction(get_response)
        
    def process_request(self, request):
        """
        Log form submissions if in debug mode
        """
        if not settings.DEBUG:
            return None

        # Only log POST/PUT/PATCH requests
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return None

        # Skip media/file uploads as they can be large
        content_type = request.META.get('CONTENT_TYPE', '')
        if 'multipart/form-data' in content_type:
            logger.debug(f"[FormLogging] Multipart form data submission to {request.path} (not logging details)")
            return None

        # Try to log form data for regular form submissions
        try:
            # Don't try to parse empty body
            if not request.body:
                return None
                
            # For JSON data
            if 'application/json' in content_type:
                data = json.loads(request.body)
                # Mask sensitive information
                masked_data = self._mask_sensitive_data(data)
                logger.debug(f"[FormLogging] JSON submission to {request.path}: {masked_data}")
            # For regular form data
            elif request.POST:
                masked_data = self._mask_sensitive_data(dict(request.POST))
                logger.debug(f"[FormLogging] Form submission to {request.path}: {masked_data}")
        except Exception as e:
            logger.debug(f"[FormLogging] Could not log form data: {str(e)}")
        
        return None
        
    def _mask_sensitive_data(self, data):
        """
        Mask sensitive data before logging
        """
        if not isinstance(data, dict):
            return data
            
        # Sensitive field names to mask
        sensitive_fields = [
            'password', 'password1', 'password2', 'new_password', 
            'old_password', 'confirm_password', 'verification_code',
            'reset_code', 'secret', 'token', 'api_key', 'credit_card',
            'card_number', 'cvv', 'ssn'
        ]
        
        # Create a copy to avoid modifying the original
        masked_data = data.copy()
        
        # Mask sensitive fields
        for key in masked_data:
            if any(sf in key.lower() for sf in sensitive_fields):
                masked_data[key] = '********'
                
        return masked_data

    async def __call__(self, request):
        """Handle both sync and async calls"""
        # Process request
        response = self.process_request(request)
        if response is not None:
            return response
        
        # Get response from the next middleware/view
        if self.is_async:
            response = await self.get_response(request)
        else:
            response = self.get_response(request)
            
        # If response is a coroutine, await it
        if asyncio.iscoroutine(response):
            response = await response
            
        return response


def track_successful_login(user, request):
    """
    Track successful login and detect suspicious activity
    To be called from the login view after successful authentication
    """
    try:
        # Get IP and user agent from request
        ip_address = getattr(request, 'client_ip', request.META.get('REMOTE_ADDR', '0.0.0.0'))
        user_agent = getattr(request, 'user_agent', request.META.get('HTTP_USER_AGENT', 'Unknown'))

        # Check if this is a new device/location for this user
        # This is a placeholder - in a real app, you'd have a model to track user's devices
        is_new_device = True  # For demonstration

        # If it's a new device/location, send an alert email
        if is_new_device:
            logger.info(f"New login for {user.email} from IP: {ip_address}, User-Agent: {user_agent}")

            # Send alert email (should be done asynchronously in production)
            if not settings.DEBUG:  # Only send in non-debug mode
                try:
                    send_login_alert_email(
                        user.email,
                        ip_address=ip_address,
                        device_info=user_agent,
                        location=None  # Would require IP geolocation lookup
                    )
                except Exception as e:
                    logger.error(f"Failed to send login alert: {str(e)}")

        # Update the user's last login details
        # In a real app, you'd store this in a model

    except Exception as e:
        logger.error(f"Error tracking login: {str(e)}")
        # Don't interrupt the login process, just log the error