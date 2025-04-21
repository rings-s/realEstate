# Path: accounts/utils.py
# Utility functions for email, responses, rate limiting, and debugging for the Real Estate Auction Platform.

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.utils.html import strip_tags
from django.core.cache import cache
from typing import Dict, Any, Optional, List, Union # Added Union
import logging
from django.utils import timezone
from django.utils.translation import gettext_lazy as _ # For potential translations in messages
from rest_framework import status
from rest_framework.response import Response
from functools import wraps
import ipaddress # For potential IP validation (optional)

logger = logging.getLogger(__name__)

# --- Constants ---
# Define rate limiting parameters (configurable via settings.py)
MAX_EMAIL_ATTEMPTS = getattr(settings, 'MAX_EMAIL_ATTEMPTS', 5) # General email limit
EMAIL_LOCKOUT_TIME = getattr(settings, 'EMAIL_LOCKOUT_TIME_SECONDS', 60 * 15) # 15 minutes lockout for general emails
MAX_VERIFICATION_ATTEMPTS = getattr(settings, 'MAX_VERIFICATION_ATTEMPTS', 3) # Specific limit for verification
VERIFICATION_LOCKOUT_TIME = getattr(settings, 'VERIFICATION_LOCKOUT_TIME_SECONDS', 60 * 30) # 30 minutes lockout for verification
MAX_RESET_ATTEMPTS = getattr(settings, 'MAX_RESET_ATTEMPTS', 3) # Specific limit for password reset
RESET_LOCKOUT_TIME = getattr(settings, 'RESET_LOCKOUT_TIME_SECONDS', 60 * 30) # 30 minutes lockout for password reset

# --- Custom Exceptions ---
class EmailRateLimitExceeded(Exception):
    """Custom exception raised when an email action exceeds its rate limit."""
    def __init__(self, message=None, wait_minutes=None):
        self.wait_minutes = wait_minutes
        default_message = _("Too many attempts. Please try again later.")
        if wait_minutes:
            # Translators: {wait_minutes} is the number of minutes to wait.
            default_message = _("Too many attempts. Please wait {wait_minutes} minutes before trying again.").format(wait_minutes=wait_minutes)
        super().__init__(message or default_message)


# --- API Response Helper ---
def create_response(
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    error_code: Optional[str] = None,
    status_code: int = status.HTTP_200_OK
) -> Response:
    """
    Creates a standardized JSON response for API endpoints using DRF Response.

    Args:
        data: Dictionary containing the primary data payload (if successful).
        message: A success or informational message.
        error: An error message (if request failed).
        error_code: A specific code identifying the error (optional).
        status_code: The HTTP status code for the response.

    Returns:
        A DRF Response object.
    """
    response_data: Dict[str, Any] = {"status": "error" if error else "success"}

    if data is not None:
        response_data["data"] = data # Nest data under a 'data' key
    if message:
        response_data["message"] = message
    if error:
        response_data["error"] = {"message": error} # Nest error details
        if error_code:
           response_data["error"]["code"] = error_code

    return Response(response_data, status=status_code)

# --- Rate Limiting Helper ---
def check_email_rate_limit(email: str, action_type: str) -> None:
    """
    Checks and increments the rate limit counter for a given email and action.
    Uses Django's cache framework.

    Args:
        email: The user's email address (or other identifier).
        action_type: A string identifying the action being rate-limited
                     (e.g., 'verification', 'reset', 'login_alert').

    Raises:
        EmailRateLimitExceeded: If the rate limit for the action has been exceeded.
    """
    if not email:
        logger.warning(f"Attempted rate limit check with empty email for action: {action_type}")
        return # Silently ignore or raise ValueError('Email cannot be empty')

    # Determine limits and lockout time based on action type
    limits = {
        'verification': (MAX_VERIFICATION_ATTEMPTS, VERIFICATION_LOCKOUT_TIME),
        'reset': (MAX_RESET_ATTEMPTS, RESET_LOCKOUT_TIME),
        # Add other specific actions if needed
        'default': (MAX_EMAIL_ATTEMPTS, EMAIL_LOCKOUT_TIME) # Fallback for general actions
    }
    max_attempts, lockout_time = limits.get(action_type, limits['default'])

    # Construct a normalized cache key
    # Ensure email is lowercased and potentially problematic characters are replaced
    normalized_email = email.lower().replace('@', '_at_').replace('.', '_dot_')
    cache_key = f"rate_limit_{action_type}_{normalized_email}"

    # Get current attempt count from cache
    attempts = cache.get(cache_key, 0)

    # Check if limit is exceeded
    if attempts >= max_attempts:
        ttl = cache.ttl(cache_key) # Get remaining lockout time in seconds
        wait_minutes = (ttl // 60) + 1 if ttl else (lockout_time // 60) # Calculate wait time in minutes
        logger.warning(f"Rate limit exceeded for action '{action_type}' by {email}. Attempts: {attempts}/{max_attempts}.")
        raise EmailRateLimitExceeded(wait_minutes=wait_minutes)

    # Increment attempts and reset timeout using cache
    try:
        # Atomically increment if supported by backend, otherwise set with timeout
        # cache.incr(cache_key) might require setting it first if it doesn't exist
        cache.set(cache_key, attempts + 1, timeout=lockout_time)
        logger.debug(f"Rate limit attempt {attempts + 1}/{max_attempts} for action '{action_type}' by {email}.")
    except Exception as e:
        logger.error(f"Failed to update cache for rate limiting key {cache_key}: {e}", exc_info=True)
        # Decide how to handle cache failures: fail open (allow action) or closed (block action)?
        # Failing open might be better for user experience unless security dictates otherwise.


# --- Core Email Sending Helper ---
def send_templated_email(
    email: str,
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    fail_silently: bool = False
) -> bool:
    """
    Sends an email using Django templates for HTML and plain text versions.

    Args:
        email: Recipient email address.
        subject: Email subject line (company name will be prepended).
        template_name: Base name of the template file (e.g., 'verification_email').
                       Expects 'emails/{template_name}.html' and potentially 'emails/{template_name}.txt'.
        context: Dictionary containing data for template rendering.
        fail_silently: If True, suppresses exceptions during email sending (logs instead).

    Returns:
        bool: True if the email was sent or logged successfully, False otherwise.
    """
    if not email:
        logger.error(f"Attempted to send email with empty recipient address (Subject: {subject})")
        return False

    # Add common context variables from settings
    company_name = getattr(settings, 'COMPANY_NAME', 'Real Estate Auction Platform')
    default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com') # Ensure a default
    support_email = getattr(settings, 'SUPPORT_EMAIL', default_from_email)
    frontend_url = getattr(settings, 'FRONTEND_URL', '').rstrip('/') # Ensure no trailing slash

    context.update({
        'company_name': company_name,
        'company_address': getattr(settings, 'COMPANY_ADDRESS', ''),
        'company_contact': getattr(settings, 'COMPANY_CONTACT', ''),
        'support_email': support_email,
        'frontend_url': frontend_url, # Make base URL available in templates
        'current_year': timezone.now().year, # For footers
    })

    # Construct subject
    full_subject = f"[{company_name}] {subject}"

    try:
        # Render HTML message
        html_template_path = f'emails/{template_name}.html'
        html_message = render_to_string(html_template_path, context)

        # Render or create plain text message
        try:
            txt_template_path = f'emails/{template_name}.txt'
            plain_message = render_to_string(txt_template_path, context)
        except TemplateDoesNotExist:
            logger.debug(f"Plain text template {txt_template_path} not found, generating from HTML.")
            plain_message = strip_tags(html_message) # Generate plain text from HTML

    except TemplateDoesNotExist as e:
        logger.error(f"Email template not found: {e}. Cannot send email '{subject}' to {email}.")
        if not fail_silently:
             raise
        return False
    except Exception as template_error:
        logger.error(f"Failed to render email template '{template_name}' for {email}: {template_error}", exc_info=True)
        if not fail_silently:
             raise
        return False

    # Handle console backend in DEBUG mode for development visibility
    is_console_backend = getattr(settings, 'EMAIL_BACKEND', '').endswith('.console.EmailBackend')
    if settings.DEBUG and is_console_backend:
        border = "=" * 80
        # Log essential context keys for debugging, avoid logging raw codes if possible outside specific dev logs
        context_summary = {k: v for k, v in context.items() if k not in ['verification_code', 'reset_code'] or settings.DEBUG}
        logger.info(f"\n{border}\n"
                    f"--- CONSOLE EMAIL (SIMULATED SEND) ---\n"
                    f"TO: {email}\n"
                    f"FROM: {default_from_email}\n"
                    f"SUBJECT: {full_subject}\n"
                    f"TEMPLATE: {template_name}\n"
                    # f"CONTEXT: {context_summary}\n" # Optional: Log non-sensitive context
                    f"-- PLAIN TEXT --\n{plain_message}\n"
                    # f"-- HTML --\n{html_message[:1000]}...\n" # Optional: Log start of HTML
                    f"{border}")
        return True # Email was "sent" to console

    # Send the actual email using Django's send_mail function
    try:
        send_mail(
            subject=full_subject,
            message=plain_message,
            html_message=html_message,
            from_email=default_from_email,
            recipient_list=[email],
            fail_silently=fail_silently # Let send_mail handle basic errors if fail_silently
        )
        logger.info(f"Email '{subject}' sent successfully to {email} via backend.")
        return True
    except Exception as e:
        # Log error even if fail_silently is True, as send_mail might suppress it
        logger.error(f"Failed to send email '{subject}' to {email} via backend: {e}", exc_info=True)
        if not fail_silently:
            raise # Re-raise the exception if sending is critical
        return False


# --- Specific Email Function Wrappers ---

def send_verification_email(
    email: str,
    verification_code: str,
    context: Optional[Dict[str, Any]] = None,
    user_name: Optional[str] = None
) -> None:
    """Sends the email verification code."""
    action_type = 'verification'
    try:
        if settings.DEBUG:
            logger.info(f"DEV_INFO: Verification code for {email}: {verification_code}")

        check_email_rate_limit(email, action_type)

        local_context = context if context is not None else {}
        # Calculate expiry in hours based on lockout time for display
        expiry_hours = VERIFICATION_LOCKOUT_TIME // 3600
        local_context.update({
            'verification_code': verification_code,
            'user_name': user_name or email,
            'expiry_hours': expiry_hours
        })

        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            verify_path = getattr(settings, 'EMAIL_VERIFY_PATH', '/verify-email') # Configurable path
            local_context['verification_url'] = f"{frontend_url.rstrip('/')}{verify_path}/{verification_code}"

        send_templated_email(
            email=email,
            subject="Verify Your Email Address",
            template_name='verification_email',
            context=local_context,
            fail_silently=False # Verification is critical
        )
    except EmailRateLimitExceeded:
        logger.warning(f"Rate limit hit for {action_type} email to {email}.")
        raise
    except Exception as e:
        logger.exception(f"Failed to send {action_type} email to {email}: {e}")
        if not settings.DEBUG: # Don't break dev flow, but raise in prod
            raise


def send_password_reset_email(
    email: str,
    reset_code: str,
    context: Optional[Dict[str, Any]] = None,
    user_name: Optional[str] = None
) -> None:
    """Sends the password reset code."""
    action_type = 'reset'
    try:
        if settings.DEBUG:
            logger.info(f"DEV_INFO: Password reset code for {email}: {reset_code}")

        check_email_rate_limit(email, action_type)

        local_context = context if context is not None else {}
        expiry_hours = RESET_LOCKOUT_TIME // 3600
        local_context.update({
            'reset_code': reset_code,
            'user_name': user_name or email,
            'expiry_hours': expiry_hours
        })

        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            reset_path = getattr(settings, 'PASSWORD_RESET_PATH', '/reset-password') # Configurable path
            local_context['reset_url'] = f"{frontend_url.rstrip('/')}{reset_path}/{reset_code}"

        send_templated_email(
            email=email,
            subject="Reset Your Password",
            template_name='password_reset',
            context=local_context,
            fail_silently=False # Password reset is critical
        )
    except EmailRateLimitExceeded:
        logger.warning(f"Rate limit hit for {action_type} email to {email}.")
        raise
    except Exception as e:
        logger.exception(f"Failed to send {action_type} email to {email}: {e}")
        if not settings.DEBUG:
            raise


def send_login_alert_email(
    email: str,
    ip_address: Optional[str] = None,
    location: Optional[str] = None,
    device_info: Optional[str] = None,
    login_time: Optional[Any] = None
) -> None:
    """Sends an alert for a potentially new login."""
    action_type = 'login_alert'
    try:
        # Optional: Apply rate limiting to login alerts if they become noisy
        # check_email_rate_limit(email, action_type)

        context = {
            'ip_address': ip_address or 'Not available',
            'location': location or 'Unknown location',
            'device_info': device_info or 'Unknown device',
            'login_time': login_time or timezone.now(),
            'user_email': email # Pass email for context if needed
        }

        send_templated_email(
            email=email,
            subject="Security Alert: New Login Detected",
            template_name='login_alert',
            context=context,
            fail_silently=True # Non-critical notification
        )
    # except EmailRateLimitExceeded:
    #     logger.warning(f"Rate limit hit for {action_type} email to {email}.")
        # Don't raise, fail silently
    except Exception as e:
        # Error is logged by send_templated_email if fail_silently=True
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


def send_bid_confirmation_email(
    email: str,
    property_title: str,
    bid_amount: Union[float, int],
    currency: str,
    auction_id: Optional[str] = None # Added auction ID
) -> None:
    """Sends a bid confirmation email."""
    action_type = 'bid_confirmation'
    try:
        context = {
            'property_title': property_title,
            'bid_amount': bid_amount,
            'currency': currency,
            'bid_time': timezone.now(),
        }
        # Add auction link if ID and frontend URL are available
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url and auction_id:
            auction_path = getattr(settings, 'AUCTION_DETAIL_PATH', '/auctions') # Configurable path
            context['auction_url'] = f"{frontend_url.rstrip('/')}{auction_path}/{auction_id}"

        send_templated_email(
            email=email,
            subject="Your Bid Has Been Placed",
            template_name='bid_confirmation',
            context=context,
            fail_silently=True # Usually non-critical
        )
    except Exception as e:
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


def send_role_assignment_email(
    email: str,
    role_names: List[str], # List of display names
    added_roles: Optional[List[str]] = None,
    removed_roles: Optional[List[str]] = None
) -> None:
    """Sends notification when user roles are updated."""
    action_type = 'role_assignment'
    try:
        context = {
            'roles': role_names,
            'added_roles': added_roles or [],
            'removed_roles': removed_roles or [],
            'has_changes': bool(added_roles or removed_roles),
            'assignment_time': timezone.now(),
        }

        send_templated_email(
            email=email,
            subject="Your Account Roles Have Been Updated",
            template_name='role_assignment',
            context=context,
            fail_silently=True # Non-critical notification
        )
    except Exception as e:
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


def send_inspection_request_email(
    email: str,
    property_title: str,
    property_id: str,
    deadline: Optional[Any] = None,
    urgent: bool = False,
    requester_name: Optional[str] = None # Added requester info
) -> None:
    """Sends email to inspector about property needing inspection."""
    action_type = 'inspection_request'
    try:
        context = {
            'property_title': property_title,
            'property_id': property_id,
            'deadline': deadline,
            'urgent': urgent,
            'requester_name': requester_name or 'System',
            'request_time': timezone.now(),
        }
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            inspect_path = getattr(settings, 'PROPERTY_INSPECT_PATH', '/properties') # Configurable path
            context['inspection_url'] = f"{frontend_url.rstrip('/')}{inspect_path}/{property_id}/inspect"

        subject = "Urgent Property Inspection Request" if urgent else "Property Inspection Request"

        send_templated_email(
            email=email,
            subject=subject,
            template_name='inspection_request',
            context=context,
            fail_silently=True # Operational notification, usually non-critical to user flow
        )
    except Exception as e:
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


def send_legal_review_email(
    email: str,
    contract_title: str,
    contract_id: str,
    parties: List[Dict[str, str]],
    property_address: str,
    deadline: Optional[Any] = None,
    requester_name: Optional[str] = None # Added requester info
) -> None:
    """Sends email to legal representative about contract needing review."""
    action_type = 'legal_review_request'
    try:
        context = {
            'contract_title': contract_title,
            'contract_id': contract_id,
            'parties': parties,
            'property_address': property_address,
            'deadline': deadline,
            'requester_name': requester_name or 'System',
            'request_time': timezone.now(),
        }
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            review_path = getattr(settings, 'CONTRACT_REVIEW_PATH', '/contracts') # Configurable path
            context['review_url'] = f"{frontend_url.rstrip('/')}{review_path}/{contract_id}/review"

        send_templated_email(
            email=email,
            subject="Real Estate Contract Review Request",
            template_name='legal_review',
            context=context,
            fail_silently=True # Operational notification
        )
    except Exception as e:
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


def send_dispute_notification_email(
    email: str,
    transaction_id: str,
    property_title: str,
    dispute_reason: str,
    is_legal_rep: bool = False,
    disputer_name: Optional[str] = None # Added disputer info
) -> None:
    """Sends notification about a dispute."""
    action_type = 'dispute_notification'
    try:
        context = {
            'transaction_id': transaction_id,
            'property_title': property_title,
            'dispute_reason': dispute_reason,
            'is_legal_rep': is_legal_rep,
            'disputer_name': disputer_name or 'A user',
            'dispute_time': timezone.now(),
        }
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            dispute_path = getattr(settings, 'TRANSACTION_DISPUTE_PATH', '/transactions') # Configurable path
            context['dispute_url'] = f"{frontend_url.rstrip('/')}{dispute_path}/{transaction_id}/dispute"

        template = 'dispute_notification_legal' if is_legal_rep else 'dispute_notification'

        send_templated_email(
            email=email,
            subject="Real Estate Transaction Dispute Notification",
            template_name=template,
            context=context,
            fail_silently=True # Notification
        )
    except Exception as e:
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


def send_auction_status_change_email(
    email: str,
    property_title: str,
    auction_id: str,
    old_status: str,
    new_status: str,
    role: str # User's role relative to auction (seller, buyer, agent, etc.)
) -> None:
    """Sends notification about auction status change."""
    action_type = 'auction_status_change'
    try:
        context = {
            'property_title': property_title,
            'auction_id': auction_id,
            'old_status': old_status,
            'new_status': new_status,
            'role': role,
            'change_time': timezone.now(),
        }
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            auction_path = getattr(settings, 'AUCTION_DETAIL_PATH', '/auctions')
            context['auction_url'] = f"{frontend_url.rstrip('/')}{auction_path}/{auction_id}"

        send_templated_email(
            email=email,
            subject=f"Property Auction Status Update: {new_status}",
            template_name='auction_status_change',
            context=context,
            fail_silently=True # Notification
        )
    except Exception as e:
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


def send_outbid_notification_email(
    email: str,
    property_title: str,
    auction_id: str,
    previous_bid: Union[float, int],
    current_bid: Union[float, int],
    currency: str,
    end_time: Any # Datetime object or string
) -> None:
    """Sends notification when user is outbid."""
    action_type = 'outbid_notification'
    try:
        context = {
            'property_title': property_title,
            'auction_id': auction_id,
            'previous_bid': previous_bid,
            'current_bid': current_bid,
            'currency': currency,
            'end_time': end_time,
            'outbid_time': timezone.now(),
        }
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            auction_path = getattr(settings, 'AUCTION_DETAIL_PATH', '/auctions')
            context['auction_url'] = f"{frontend_url.rstrip('/')}{auction_path}/{auction_id}"

        send_templated_email(
            email=email,
            subject="You've Been Outbid on a Property",
            template_name='outbid_notification',
            context=context,
            fail_silently=True # Common notification, non-critical
        )
    except Exception as e:
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


def send_auction_won_email(
    email: str,
    property_title: str,
    property_address: str,
    auction_id: str,
    winning_bid: Union[float, int],
    currency: str,
    next_steps: List[Dict[str, str]] # List of steps with 'title', 'description'
) -> None:
    """Sends notification to the winning bidder."""
    action_type = 'auction_won'
    try:
        context = {
            'property_title': property_title,
            'property_address': property_address,
            'auction_id': auction_id,
            'winning_bid': winning_bid,
            'currency': currency,
            'next_steps': next_steps,
            'win_time': timezone.now(),
        }
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            auction_path = getattr(settings, 'AUCTION_DETAIL_PATH', '/auctions')
            checkout_path = getattr(settings, 'CHECKOUT_PATH', '/checkout') # Configurable path
            context['auction_url'] = f"{frontend_url.rstrip('/')}{auction_path}/{auction_id}"
            context['checkout_url'] = f"{frontend_url.rstrip('/')}{checkout_path}/{auction_id}" # Example

        send_templated_email(
            email=email,
            subject="Congratulations! You Won the Property Auction",
            template_name='auction_won',
            context=context,
            fail_silently=False # Important notification, should ideally succeed
        )
    except Exception as e:
        logger.exception(f"Failed to send {action_type} email to {email}: {e}")
        # Decide if raising is needed based on business logic


def send_auction_ended_seller_email(
    email: str,
    property_title: str,
    property_address: str,
    auction_id: str,
    final_bid: Optional[Union[float, int]], # Can be None if no bids
    currency: str,
    winner_info: Optional[Dict[str, str]] = None, # e.g., {'name': 'Winner Name', 'email': '...'}
    has_bids: bool = True
) -> None:
    """Sends notification to the seller when their property auction ends."""
    action_type = 'auction_ended_seller'
    try:
        context = {
            'property_title': property_title,
            'property_address': property_address,
            'auction_id': auction_id,
            'final_bid': final_bid,
            'currency': currency,
            'winner_info': winner_info,
            'has_bids': has_bids,
            'end_time': timezone.now(),
        }
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            auction_path = getattr(settings, 'AUCTION_DETAIL_PATH', '/auctions')
            context['auction_url'] = f"{frontend_url.rstrip('/')}{auction_path}/{auction_id}"

        subject = "Your Property Auction Has Ended Successfully" if has_bids and final_bid is not None else "Your Property Auction Has Ended"

        send_templated_email(
            email=email,
            subject=subject,
            template_name='auction_ended_seller',
            context=context,
            fail_silently=False # Important for seller
        )
    except Exception as e:
        logger.exception(f"Failed to send {action_type} email to seller {email}: {e}")


def send_property_viewing_request_email(
    email: str, # Seller or agent email
    property_title: str,
    property_address: str,
    requester_name: str,
    requested_date: Any, # String or datetime
    requester_contact: str,
    property_id: str,
    requester_email: Optional[str] = None # Added requester email
) -> None:
    """Sends notification about property viewing request."""
    action_type = 'property_viewing_request'
    try:
        context = {
            'property_title': property_title,
            'property_address': property_address,
            'requester_name': requester_name,
            'requester_email': requester_email,
            'requested_date': requested_date,
            'requester_contact': requester_contact,
            'property_id': property_id,
            'request_time': timezone.now(),
        }
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            property_path = getattr(settings, 'PROPERTY_DETAIL_PATH', '/properties') # Configurable path
            context['property_url'] = f"{frontend_url.rstrip('/')}{property_path}/{property_id}"

        send_templated_email(
            email=email,
            subject=f"Property Viewing Request for: {property_title}",
            template_name='property_viewing_request',
            context=context,
            fail_silently=True # Operational notification
        )
    except Exception as e:
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


def send_contract_signed_email(
    email: str, # Recipient (other party, agent, etc.)
    contract_title: str,
    contract_id: str,
    property_address: str,
    signer_name: str,
    signer_role: str,
    is_complete: bool = False # True if all parties have signed
) -> None:
    """Sends notification when a real estate contract is signed."""
    action_type = 'contract_signed'
    try:
        context = {
            'contract_title': contract_title,
            'contract_id': contract_id,
            'property_address': property_address,
            'signer_name': signer_name,
            'signer_role': signer_role,
            'is_complete': is_complete,
            'sign_time': timezone.now(),
        }
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            contract_path = getattr(settings, 'CONTRACT_DETAIL_PATH', '/contracts') # Configurable path
            context['contract_url'] = f"{frontend_url.rstrip('/')}{contract_path}/{contract_id}"

        subject = "Real Estate Contract Fully Executed" if is_complete else f"Real Estate Contract Signed by {signer_role}"

        send_templated_email(
            email=email,
            subject=subject,
            template_name='contract_signed',
            context=context,
            fail_silently=True # Notification, potentially important but non-blocking
        )
    except Exception as e:
        logger.warning(f"Attempted to send {action_type} email to {email} but failed (error logged).")


# --- Debugging Decorator ---
def debug_request(func):
    """
    Decorator logs request details (method, path, headers, query params, masked body)
    if settings.DEBUG is True. Uses DRF request attributes if available.
    """
    @wraps(func) # Preserves function metadata (important for DRF, etc.)
    def wrapper(request, *args, **kwargs):
        # Execute wrapped function first to allow it to potentially modify request
        response = func(request, *args, **kwargs)

        # Log details only if in DEBUG mode
        if not settings.DEBUG:
            return response # Skip logging if not DEBUG

        try:
            prefix = "DEBUG_REQUEST:"
            # Basic Info
            logger.debug(f"{prefix} {request.method} {request.get_full_path()}") # Use get_full_path for query params

            # User Info
            user_info = f"User: {request.user}" if hasattr(request, 'user') and request.user.is_authenticated else "User: Anonymous"
            logger.debug(f"{prefix} {user_info}")

            # Headers (Redact sensitive ones)
            headers = {k: ('[REDACTED]' if k.lower() in ['cookie', 'authorization', 'x-csrftoken', 'proxy-authorization'] else v)
                       for k, v in request.META.items() if k.startswith('HTTP_') or k in ['CONTENT_TYPE', 'CONTENT_LENGTH', 'REMOTE_ADDR']}
            logger.debug(f"{prefix} HEADERS: {headers}")

            # Request Body (for POST, PUT, PATCH, DELETE) - Prefers request.data (DRF)
            data_to_log = None
            log_source = None
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                content_type = request.META.get('CONTENT_TYPE', '').lower()
                if 'multipart/form-data' in content_type:
                    log_source = "Multipart form data (keys logged)"
                    # Log file keys and non-file field keys from request.POST/request.data
                    if hasattr(request, 'data') and request.data:
                        data_to_log = {k: '[FILE]' if hasattr(v, 'read') else v for k, v in request.data.items()}
                    elif request.POST:
                        data_to_log = {k: v for k, v in request.POST.items()}
                        if request.FILES:
                             data_to_log.update({k: '[FILE]' for k in request.FILES.keys()})

                elif hasattr(request, 'data') and request.data: # DRF request.data (handles JSON, form, etc.)
                    data_to_log = request.data
                    log_source = "request.data"
                elif 'application/json' in content_type and hasattr(request, 'body') and request.body: # Raw JSON body
                    try:
                        data_to_log = json.loads(request.body)
                        log_source = "request.body (JSON)"
                    except json.JSONDecodeError:
                        logger.debug(f"{prefix} BODY: Invalid JSON received: {request.body[:500]}")
                elif request.POST: # Standard Django request.POST
                    data_to_log = request.POST.dict()
                    log_source = "request.POST"
                 # Add handling for other content types if necessary (e.g., XML)

            # Mask sensitive fields in the collected data before logging
            if data_to_log is not None:
                # Local masking function for simplicity
                def _mask_sensitive_data(data):
                    if isinstance(data, dict):
                        masked = {}
                        # More comprehensive list of sensitive keywords
                        sensitive_keywords = [
                            'password', 'token', 'secret', 'authorization', 'cookie', 'cvv',
                            'card_number', 'cardnumber', 'apikey', 'api_key', 'access_key',
                            'secret_key', 'sessionid', 'csrf', 'verification_code', 'reset_code', 'ssn'
                        ]
                        for k, v in data.items():
                            key_lower = str(k).lower() # Ensure key is string for lower()
                            if any(s in key_lower for s in sensitive_keywords):
                                masked[k] = '[REDACTED]'
                            elif isinstance(v, dict):
                                masked[k] = _mask_sensitive_data(v) # Recurse dicts
                            elif isinstance(v, list):
                                # Recurse lists containing dicts
                                masked[k] = [_mask_sensitive_data(i) if isinstance(i, dict) else i for i in v]
                            else:
                                masked[k] = v # Keep non-sensitive, non-structured data
                        return masked
                    elif isinstance(data, list): # Handle top-level lists
                         return [_mask_sensitive_data(i) if isinstance(i, dict) else i for i in data]
                    return data # Return non-dicts/lists as is

                # Ensure data is mutable for masking if needed (e.g., QueryDict -> dict)
                data_copy = data_to_log
                if not isinstance(data_to_log, (dict, list)):
                     try:
                          data_copy = dict(data_to_log)
                     except (TypeError, ValueError):
                          data_copy = str(data_to_log) # Fallback

                masked_data = _mask_sensitive_data(data_copy)
                log_str = f"BODY ({log_source}): {masked_data}"
                # Truncate very long logs
                if len(log_str) > 2000:
                    log_str = f"{log_str[:2000]}... [TRUNCATED]"
                logger.debug(f"{prefix} {log_str}")

            # Log Response Status (optional, might duplicate middleware logs)
            # if hasattr(response, 'status_code'):
            #     logger.debug(f"{prefix} RESPONSE STATUS: {response.status_code}")

        except Exception as e:
            logger.exception(f"Error occurred within debug_request decorator for {request.path_info}: {e}")

        return response # Return the original response
    return wrapper
