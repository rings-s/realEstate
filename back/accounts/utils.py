from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.cache import cache
from typing import Dict, Any, Optional, List
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from functools import wraps


logger = logging.getLogger(__name__)

# Constants for rate limiting
MAX_EMAIL_ATTEMPTS = 5
EMAIL_LOCKOUT_TIME = 60 * 15  # 15 minutes
MAX_VERIFICATION_ATTEMPTS = 3
VERIFICATION_LOCKOUT_TIME = 60 * 30  # 30 minutes


class EmailRateLimitExceeded(Exception):
    pass

def create_response(data=None, message=None, error=None, error_code=None, status_code=status.HTTP_200_OK):
    """
    Standardized response creator for API endpoints
    """
    response_data = {"status": "error" if error else "success"}

    if data:
        response_data.update(data)
    if message:
        response_data["message"] = message
    if error:
        response_data["error"] = error
    if error_code:
        response_data["code"] = error_code

    return Response(response_data, status=status_code)

def check_email_rate_limit(email: str, action_type: str) -> bool:
    """
    Check if email has exceeded rate limit for specific action

    Args:
        email: User's email address
        action_type: Type of action ('verification', 'reset', etc.)

    Returns:
        bool: True if rate limit is exceeded

    Raises:
        EmailRateLimitExceeded: If rate limit is exceeded
    """
    cache_key = f"{action_type}_attempts_{email}"
    attempts = cache.get(cache_key, 0)

    if action_type == 'verification' and attempts >= MAX_VERIFICATION_ATTEMPTS:
        raise EmailRateLimitExceeded(
            f"Too many verification attempts. Please wait {VERIFICATION_LOCKOUT_TIME//60} minutes."
        )
    elif action_type == 'reset' and attempts >= MAX_EMAIL_ATTEMPTS:
        raise EmailRateLimitExceeded(
            f"Too many reset attempts. Please wait {EMAIL_LOCKOUT_TIME//60} minutes."
        )

    cache.set(
        cache_key,
        attempts + 1,
        EMAIL_LOCKOUT_TIME if action_type == 'reset' else VERIFICATION_LOCKOUT_TIME
    )
    return False


def send_templated_email(
    email: str,
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    fail_silently: bool = False
) -> None:
    """
    Send an email using a template

    Args:
        email: Recipient email address
        subject: Email subject
        template_name: Name of the template to use
        context: Context data for the template
        fail_silently: Whether to suppress email sending errors
    """
    try:
        company_name = getattr(settings, 'COMPANY_NAME', 'Real Estate Auction Platform')
        context.update({
            'company_name': company_name,
            'company_address': getattr(settings, 'COMPANY_ADDRESS', ''),
            'company_contact': getattr(settings, 'COMPANY_CONTACT', ''),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', ''))
        })

        try:
            html_message = render_to_string(f'emails/{template_name}.html', context)
            plain_message = strip_tags(html_message)
        except Exception as template_error:
            logger.warning(f"Failed to render email template: {str(template_error)}")
            # Fallback to basic template
            html_message = f"<html><body><h1>{company_name}</h1><p>{subject}</p></body></html>"
            for key, value in context.items():
                if isinstance(value, (str, int, float)) and key != 'company_name':
                    html_message += f"<p>{key}: {value}</p>"
            plain_message = strip_tags(html_message)

        # For development environments, log emails instead of sending if using console backend
        if settings.DEBUG and getattr(settings, 'EMAIL_BACKEND', '') == 'django.core.mail.backends.console.EmailBackend':
            logger.info(f"Would send email to {email} with subject: {subject}")
            logger.info(f"Email content: {plain_message[:500]}...")
            return True  # Indicate that the email was logged

        send_mail(
            subject=f"{company_name} - {subject}",
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=fail_silently
        )

    except Exception as e:
        logger.error(f"Failed to send email ({template_name}) to {email}: {str(e)}")
        if not fail_silently:
            raise


def send_verification_email(
    email: str,
    verification_code: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Send verification email with code

    Args:
        email: User's email address
        verification_code: Verification code
        context: Additional context for email template
    """
    try:
        # In development mode, always display verification code in logs
        if settings.DEBUG:
            logger.info(f"DEVELOPMENT MODE - Verification code for {email}: {verification_code}")

        check_email_rate_limit(email, 'verification')

        if context is None:
            context = {}

        context.update({
            'verification_code': verification_code,
            'expiry_hours': 24
        })

        # Add verification URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            context['verification_url'] = f"{frontend_url}/verify/{verification_code}"

        send_templated_email(
            email=email,
            subject="Email Verification",
            template_name='verification_email',
            context=context
        )

    except EmailRateLimitExceeded as e:
        logger.warning(f"Rate limit exceeded for verification email to {email}")
        raise
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        # Don't raise in development mode
        if not settings.DEBUG:
            raise


def send_password_reset_email(
    email: str,
    reset_code: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Send password reset email with code

    Args:
        email: User's email address
        reset_code: Password reset code
        context: Additional context for email template
    """
    try:
        # In development mode, always display reset code in logs
        if settings.DEBUG:
            logger.info(f"DEVELOPMENT MODE - Reset code for {email}: {reset_code}")

        check_email_rate_limit(email, 'reset')

        if context is None:
            context = {}

        context.update({
            'reset_code': reset_code,
            'expiry_hours': 1
        })

        # Add reset URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', None)
        if frontend_url:
            context['reset_url'] = f"{frontend_url}/reset-password/{reset_code}"

        send_templated_email(
            email=email,
            subject="Password Reset",
            template_name='password_reset',
            context=context
        )

    except EmailRateLimitExceeded as e:
        logger.warning(f"Rate limit exceeded for password reset email to {email}")
        raise
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        # Don't raise in development mode
        if not settings.DEBUG:
            raise


def send_login_alert_email(
    email: str,
    ip_address: str,
    location: Optional[str] = None,
    device_info: Optional[str] = None
) -> None:
    """
    Send alert email for new login from unknown device/location

    Args:
        email: User's email address
        ip_address: Login IP address
        location: Geographic location (if available)
        device_info: Device information (if available)
    """
    try:
        context = {
            'ip_address': ip_address,
            'location': location or 'Unknown location',
            'device_info': device_info or 'Unknown device',
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        send_templated_email(
            email=email,
            subject="New Login Alert",
            template_name='login_alert',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send login alert email to {email}: {str(e)}")
        # Don't raise exception as this is a non-critical notification


def send_bid_confirmation_email(
    email: str,
    property_title: str,
    bid_amount: float,
    currency: str
) -> None:
    """
    Send bid confirmation email

    Args:
        email: User's email address
        property_title: Title of the property
        bid_amount: Bid amount
        currency: Currency code
    """
    try:
        context = {
            'property_title': property_title,
            'bid_amount': bid_amount,
            'currency': currency,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        send_templated_email(
            email=email,
            subject="Bid Confirmation",
            template_name='bid_confirmation',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send bid confirmation email to {email}: {str(e)}")
        # Don't raise exception as this is a non-critical notification


def send_role_assignment_email(
    email: str,
    role_names: List[str],
    added_roles: Optional[List[str]] = None,
    removed_roles: Optional[List[str]] = None
) -> None:
    """
    Send notification when user roles are updated

    Args:
        email: User's email address
        role_names: Full list of current role names (display names)
        added_roles: List of newly added role names (optional)
        removed_roles: List of removed role names (optional)
    """
    try:
        context = {
            'roles': role_names,
            'added_roles': added_roles or [],
            'removed_roles': removed_roles or [],
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None,
            'has_changes': bool(added_roles or removed_roles)
        }

        send_templated_email(
            email=email,
            subject="Role Assignment Update",
            template_name='role_assignment',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send role assignment email to {email}: {str(e)}")
        # Don't raise exception as this is a notification


def send_inspection_request_email(
    email: str,
    property_title: str,
    property_id: str,
    deadline: Optional[Any] = None,
    urgent: bool = False
) -> None:
    """
    Send email to inspector about property needing inspection

    Args:
        email: Inspector's email address
        property_title: Title of the property
        property_id: ID of the property
        deadline: Optional deadline for inspection
        urgent: Whether this is an urgent request
    """
    try:
        # Add inspection URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        inspection_url = f"{frontend_url}/properties/{property_id}/inspect" if frontend_url else ''

        context = {
            'property_title': property_title,
            'property_id': property_id,
            'inspection_url': inspection_url,
            'deadline': deadline,
            'urgent': urgent,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        subject = "Urgent Property Inspection Request" if urgent else "Property Inspection Request"

        send_templated_email(
            email=email,
            subject=subject,
            template_name='inspection_request',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send inspection request email to {email}: {str(e)}")
        # Don't raise exception as this is a notification


def send_legal_review_email(
    email: str,
    contract_title: str,
    contract_id: str,
    parties: List[Dict[str, str]],
    property_address: str,
    deadline: Optional[Any] = None
) -> None:
    """
    Send email to legal representative about contract needing review

    Args:
        email: Legal representative's email address
        contract_title: Title of the contract
        contract_id: ID of the contract
        parties: List of parties involved in the contract (dicts with 'name', 'role')
        property_address: Address of the property involved
        deadline: Optional deadline for review
    """
    try:
        # Add review URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        review_url = f"{frontend_url}/contracts/{contract_id}/review" if frontend_url else ''

        context = {
            'contract_title': contract_title,
            'contract_id': contract_id,
            'review_url': review_url,
            'parties': parties,
            'property_address': property_address,
            'deadline': deadline,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        send_templated_email(
            email=email,
            subject="Real Estate Contract Review Request",
            template_name='legal_review',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send legal review email to {email}: {str(e)}")
        # Don't raise exception as this is a notification


def send_dispute_notification_email(
    email: str,
    transaction_id: str,
    property_title: str,
    dispute_reason: str,
    is_legal_rep: bool = False
) -> None:
    """
    Send notification about a dispute

    Args:
        email: User's email address
        transaction_id: ID of the disputed transaction
        property_title: Title of the property
        dispute_reason: Reason for the dispute
        is_legal_rep: Whether recipient is a legal representative
    """
    try:
        # Add dispute URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        dispute_url = f"{frontend_url}/transactions/{transaction_id}/dispute" if frontend_url else ''

        context = {
            'transaction_id': transaction_id,
            'property_title': property_title,
            'dispute_reason': dispute_reason,
            'is_legal_rep': is_legal_rep,
            'dispute_url': dispute_url,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        template = 'dispute_notification_legal' if is_legal_rep else 'dispute_notification'

        send_templated_email(
            email=email,
            subject="Real Estate Transaction Dispute Notification",
            template_name=template,
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send dispute notification email to {email}: {str(e)}")
        # Don't raise exception as this is a notification


def send_auction_status_change_email(
    email: str,
    property_title: str,
    auction_id: str,
    old_status: str,
    new_status: str,
    role: str
) -> None:
    """
    Send notification about auction status change

    Args:
        email: User's email address
        property_title: Title of the property
        auction_id: ID of the auction
        old_status: Previous auction status
        new_status: New auction status
        role: User's role in relation to this auction (seller, buyer, inspector, agent)
    """
    try:
        # Add auction URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        auction_url = f"{frontend_url}/auctions/{auction_id}" if frontend_url else ''

        context = {
            'property_title': property_title,
            'auction_id': auction_id,
            'old_status': old_status,
            'new_status': new_status,
            'role': role,
            'auction_url': auction_url,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        send_templated_email(
            email=email,
            subject=f"Property Auction Status Update: {new_status}",
            template_name='auction_status_change',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send auction status change email to {email}: {str(e)}")
        # Don't raise exception as this is a notification


def send_outbid_notification_email(
    email: str,
    property_title: str,
    auction_id: str,
    previous_bid: float,
    current_bid: float,
    currency: str,
    end_time: Any
) -> None:
    """
    Send notification when user is outbid

    Args:
        email: User's email address
        property_title: Title of the property
        auction_id: ID of the auction
        previous_bid: User's previous bid amount
        current_bid: New highest bid amount
        currency: Currency code
        end_time: Auction end time
    """
    try:
        # Add auction URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        auction_url = f"{frontend_url}/auctions/{auction_id}" if frontend_url else ''

        context = {
            'property_title': property_title,
            'auction_id': auction_id,
            'previous_bid': previous_bid,
            'current_bid': current_bid,
            'currency': currency,
            'end_time': end_time,
            'auction_url': auction_url,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        send_templated_email(
            email=email,
            subject="You've Been Outbid on a Property",
            template_name='outbid_notification',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send outbid notification email to {email}: {str(e)}")
        # Don't raise exception as this is a notification


def send_auction_won_email(
    email: str,
    property_title: str,
    property_address: str,
    auction_id: str,
    winning_bid: float,
    currency: str,
    next_steps: List[Dict[str, str]]
) -> None:
    """
    Send notification to the winning bidder

    Args:
        email: Winner's email address
        property_title: Title of the property
        property_address: Address of the property
        auction_id: ID of the auction
        winning_bid: Winning bid amount
        currency: Currency code
        next_steps: List of next steps with instructions
    """
    try:
        # Add URLs if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        auction_url = f"{frontend_url}/auctions/{auction_id}" if frontend_url else ''
        checkout_url = f"{frontend_url}/checkout/{auction_id}" if frontend_url else ''

        context = {
            'property_title': property_title,
            'property_address': property_address,
            'auction_id': auction_id,
            'winning_bid': winning_bid,
            'currency': currency,
            'next_steps': next_steps,
            'auction_url': auction_url,
            'checkout_url': checkout_url,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        send_templated_email(
            email=email,
            subject="Congratulations! You Won the Property Auction",
            template_name='auction_won',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send auction won email to {email}: {str(e)}")
        # Don't raise exception as this is a notification


def send_auction_ended_seller_email(
    email: str,
    property_title: str,
    property_address: str,
    auction_id: str,
    final_bid: float,
    currency: str,
    winner_info: Optional[Dict[str, str]] = None,
    has_bids: bool = True
) -> None:
    """
    Send notification to the seller when their property auction ends

    Args:
        email: Seller's email address
        property_title: Title of the property
        property_address: Address of the property
        auction_id: ID of the auction
        final_bid: Final bid amount
        currency: Currency code
        winner_info: Information about the winner (if any)
        has_bids: Whether the auction received any bids
    """
    try:
        # Add auction URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        auction_url = f"{frontend_url}/auctions/{auction_id}" if frontend_url else ''

        context = {
            'property_title': property_title,
            'property_address': property_address,
            'auction_id': auction_id,
            'final_bid': final_bid,
            'currency': currency,
            'winner_info': winner_info,
            'has_bids': has_bids,
            'auction_url': auction_url,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        subject = "Your Property Auction Has Ended Successfully" if has_bids else "Your Property Auction Has Ended Without Bids"

        send_templated_email(
            email=email,
            subject=subject,
            template_name='auction_ended_seller',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send auction ended email to seller {email}: {str(e)}")
        # Don't raise exception as this is a notification


def send_property_viewing_request_email(
    email: str,
    property_title: str,
    property_address: str,
    requester_name: str,
    requested_date: Any,
    requester_contact: str,
    property_id: str
) -> None:
    """
    Send notification about property viewing request

    Args:
        email: Seller's or agent's email address
        property_title: Title of the property
        property_address: Address of the property
        requester_name: Name of the person requesting viewing
        requested_date: Preferred date for viewing
        requester_contact: Contact information for the requester
        property_id: ID of the property
    """
    try:
        # Add property URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        property_url = f"{frontend_url}/properties/{property_id}" if frontend_url else ''

        context = {
            'property_title': property_title,
            'property_address': property_address,
            'requester_name': requester_name,
            'requested_date': requested_date,
            'requester_contact': requester_contact,
            'property_url': property_url,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        send_templated_email(
            email=email,
            subject="Property Viewing Request",
            template_name='property_viewing_request',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send property viewing request email to {email}: {str(e)}")
        # Don't raise exception as this is a notification


def send_contract_signed_email(
    email: str,
    contract_title: str,
    contract_id: str,
    property_address: str,
    signer_name: str,
    signer_role: str,
    is_complete: bool = False
) -> None:
    """
    Send notification when a real estate contract is signed

    Args:
        email: Recipient's email address
        contract_title: Title of the contract
        contract_id: ID of the contract
        property_address: Address of the property
        signer_name: Name of the person who signed
        signer_role: Role of the signer (buyer, seller, agent, etc.)
        is_complete: Whether all parties have signed
    """
    try:
        # Add contract URL if FRONTEND_URL is defined
        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        contract_url = f"{frontend_url}/contracts/{contract_id}" if frontend_url else ''

        context = {
            'contract_title': contract_title,
            'contract_id': contract_id,
            'property_address': property_address,
            'signer_name': signer_name,
            'signer_role': signer_role,
            'is_complete': is_complete,
            'contract_url': contract_url,
            'timestamp': timezone.now() if hasattr(settings, 'SERVER_TIMEZONE') else None
        }

        subject = "Real Estate Contract Fully Executed" if is_complete else f"Real Estate Contract Signed by {signer_role}"

        send_templated_email(
            email=email,
            subject=subject,
            template_name='contract_signed',
            context=context,
            fail_silently=True
        )

    except Exception as e:
        logger.error(f"Failed to send contract signed email to {email}: {str(e)}")


# Fixed debug_request decorator that preserves function attributes
def debug_request(func):
    """
    Decorator that logs detailed request information in debug mode
    """
    @wraps(func)  # This preserves the decorated function's attributes
    def wrapper(request, *args, **kwargs):
        if settings.DEBUG:
            # Log request details
            logger.debug(f"Request: {request.method} {request.path}")
            logger.debug(f"Headers: {dict(request.headers)}")

            # For GET requests, log query parameters
            if request.method == 'GET' and hasattr(request, 'query_params'):
                logger.debug(f"Query params: {request.query_params}")

            # For POST/PUT/PATCH, log request body (but mask sensitive data)
            elif request.method in ['POST', 'PUT', 'PATCH'] and hasattr(request, 'data'):
                data_copy = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)

                # Mask sensitive fields
                sensitive_fields = ['password', 'password_confirmation', 'current_password',
                                  'new_password', 'confirm_password', 'token', 'refresh',
                                  'access', 'verification_code', 'reset_code']

                for field in sensitive_fields:
                    if field in data_copy:
                        data_copy[field] = '[REDACTED]'

                logger.debug(f"Request body: {data_copy}")

        # Execute the actual view function
        return func(request, *args, **kwargs)
    return wrapper