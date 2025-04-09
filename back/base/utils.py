import os
import uuid
import time
import random
import string
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from accounts.models import Role


# -------------------------------------------------------------------------
# File and Image Handling Utilities
# -------------------------------------------------------------------------

def generate_unique_filename(original_filename):
    """
    Generate a unique filename while preserving the original extension.

    Args:
        original_filename (str): The original filename

    Returns:
        str: A unique filename with the same extension
    """
    ext = os.path.splitext(original_filename)[1].lower() if '.' in original_filename else ''
    unique_name = f"{uuid.uuid4()}{ext}"
    return unique_name


def create_thumbnail(image_file, size=(200, 200), format='JPEG', quality=85):
    """
    Create a thumbnail from an image file.

    Args:
        image_file: Django UploadedFile or path to image
        size (tuple): Thumbnail dimensions (width, height)
        format (str): Image format for the thumbnail
        quality (int): Compression quality (1-100)

    Returns:
        ContentFile: Django ContentFile with the thumbnail
    """
    if not image_file:
        return None

    try:
        img = Image.open(image_file)

        # Convert to RGB if needed (for PNG with transparency)
        if img.mode not in ('L', 'RGB', 'RGBA'):
            img = img.convert('RGB')

        # Create thumbnail
        img.thumbnail(size, Image.LANCZOS)

        # Save to BytesIO
        thumb_io = BytesIO()
        save_kwargs = {'format': format}
        if format in ('JPEG', 'JPG'):
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True

        img.save(thumb_io, **save_kwargs)
        thumb_io.seek(0)

        return ContentFile(thumb_io.getvalue())
    except Exception as e:
        print(f"Error creating thumbnail: {str(e)}")
        return None


def get_file_size_in_kb(file_obj):
    """
    Get file size in KB from a file object.

    Args:
        file_obj: Django File or UploadedFile object

    Returns:
        int: File size in KB or 0 if file doesn't exist
    """
    if not file_obj:
        return 0

    try:
        return file_obj.size // 1024
    except (AttributeError, IOError):
        return 0


def validate_image_file(file_obj, max_size_mb=5, allowed_extensions=None):
    """
    Validate an image file for size and format.

    Args:
        file_obj: Django File or UploadedFile object
        max_size_mb (int): Maximum file size in MB
        allowed_extensions (list): List of allowed file extensions

    Raises:
        ValidationError: If validation fails

    Returns:
        bool: True if validation passes
    """
    if not file_obj:
        return True

    # Validate size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_obj.size > max_size_bytes:
        raise ValidationError(_('حجم الملف يتجاوز الحد المسموح به (%(max_size)s ميجابايت).') % {'max_size': max_size_mb})

    # Validate extension
    if allowed_extensions:
        ext = os.path.splitext(file_obj.name)[1].lower().lstrip('.')
        if ext not in allowed_extensions:
            raise ValidationError(_('نوع الملف غير مدعوم. الأنواع المدعومة: %(ext_list)s.') % {'ext_list': ', '.join(allowed_extensions)})

    return True


# -------------------------------------------------------------------------
# String and Text Utilities
# -------------------------------------------------------------------------

def generate_random_code(length=6, chars=string.digits):
    """
    Generate a random code of specified length.

    Args:
        length (int): Length of the code
        chars (str): Characters to use for the code

    Returns:
        str: Random code
    """
    return ''.join(random.choice(chars) for _ in range(length))


def generate_slug(text, model_class, max_length=255):
    """
    Generate a unique slug for a model.

    Args:
        text (str): Text to slugify
        model_class: Django model class
        max_length (int): Maximum slug length

    Returns:
        str: Unique slug
    """
    original_slug = slugify(text)[:max_length]
    slug = original_slug

    # Check if slug already exists
    counter = 1
    while model_class.objects.filter(slug=slug).exists():
        suffix = f"-{counter}"
        slug = f"{original_slug[:max_length - len(suffix)]}{suffix}"
        counter += 1

    return slug


def sanitize_html(html_content):
    """
    Sanitize HTML content to prevent XSS attacks.
    Uses bleach library if available, or basic string replacement.

    Args:
        html_content (str): HTML content to sanitize

    Returns:
        str: Sanitized HTML content
    """
    try:
        import bleach
        allowed_tags = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attrs = {'a': ['href', 'title', 'target']}
        return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    except ImportError:
        # Basic sanitization if bleach is not available
        replacements = [
            ('<script', '&lt;script'),
            ('javascript:', 'no-script:'),
            ('onerror=', 'no-error='),
            ('onclick=', 'no-click='),
            ('onload=', 'no-load='),
            ('onmouseover=', 'no-mouseover=')
        ]
        for old, new in replacements:
            html_content = html_content.replace(old, new)
        return html_content


# -------------------------------------------------------------------------
# Date and Time Utilities
# -------------------------------------------------------------------------

def format_datetime(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format a datetime object as a string.

    Args:
        dt (datetime): Datetime object
        format_str (str): Format string

    Returns:
        str: Formatted datetime string
    """
    if not dt:
        return ""
    return dt.strftime(format_str)


def get_time_remaining(end_date):
    """
    Calculate time remaining until end_date.

    Args:
        end_date (datetime): End date

    Returns:
        dict: Time remaining in days, hours, minutes, seconds and total_seconds
    """
    if not end_date:
        return {
            'days': 0,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
            'total_seconds': 0
        }

    now = timezone.now()

    if end_date <= now:
        return {
            'days': 0,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
            'total_seconds': 0
        }

    time_left = end_date - now
    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'total_seconds': time_left.total_seconds()
    }


def is_date_in_range(date, start_date=None, end_date=None):
    """
    Check if a date is within a range.

    Args:
        date (datetime): Date to check
        start_date (datetime, optional): Start date of range
        end_date (datetime, optional): End date of range

    Returns:
        bool: True if date is in range
    """
    if not date:
        return False

    if start_date and date < start_date:
        return False

    if end_date and date > end_date:
        return False

    return True


# -------------------------------------------------------------------------
# Financial Utilities
# -------------------------------------------------------------------------

def calculate_fee(amount, percentage):
    """
    Calculate a fee based on a percentage.

    Args:
        amount (float): Base amount
        percentage (float): Fee percentage

    Returns:
        float: Fee amount
    """
    if not amount or not percentage:
        return 0

    return (amount * percentage) / 100


def format_currency(amount, currency='SAR', locale='ar_SA'):
    """
    Format a currency amount according to locale.

    Args:
        amount (float): Amount to format
        currency (str): Currency code
        locale (str): Locale to use for formatting

    Returns:
        str: Formatted currency string
    """
    if amount is None:
        return ""

    try:
        import locale as locale_module
        locale_module.setlocale(locale_module.LC_ALL, locale)
        return locale_module.currency(amount, currency, grouping=True)
    except (ImportError, locale_module.Error):
        # Basic formatting if locale module fails
        if locale.startswith('ar'):
            return f"{amount:,.2f} {currency}"
        else:
            return f"{currency} {amount:,.2f}"


def calculate_installments(total_amount, payment_count, interval_days=30):
    """
    Calculate installment amounts and dates.

    Args:
        total_amount (float): Total amount to pay
        payment_count (int): Number of installments
        interval_days (int): Interval between payments in days

    Returns:
        list: List of dictionaries with amount and due_date
    """
    if not total_amount or payment_count < 1:
        return []

    # Calculate per-payment amount, rounded to 2 decimal places
    payment_amount = round(total_amount / payment_count, 2)

    # Calculate installments
    installments = []
    start_date = timezone.now()

    for i in range(payment_count):
        due_date = start_date + timedelta(days=interval_days * (i + 1))

        # Last payment may need adjustment due to rounding
        if i == payment_count - 1:
            # Calculate the sum of all previous payments
            prev_sum = payment_amount * (payment_count - 1)
            # Adjust the last payment to make the total exact
            amount = round(total_amount - prev_sum, 2)
        else:
            amount = payment_amount

        installments.append({
            'number': i + 1,
            'amount': amount,
            'due_date': due_date
        })

    return installments


# -------------------------------------------------------------------------
# Auction and Property Utilities
# -------------------------------------------------------------------------

def check_auction_status(auction):
    """
    Check and update auction status based on dates.

    Args:
        auction: Auction object

    Returns:
        str: Current auction status
    """
    now = timezone.now()

    # Skip if status is already finalized
    if auction.status in ['completed', 'cancelled']:
        return auction.status

    # Update status based on current time
    if auction.start_date > now:
        new_status = 'scheduled'
    elif auction.end_date < now:
        new_status = 'ended'
    else:
        new_status = 'live'

    # Update if status changed
    if new_status != auction.status:
        auction.status = new_status
        auction.save(update_fields=['status'])

    return auction.status


def get_bid_increment_suggestions(current_bid, min_increment=100, count=3, factor=1.5):
    """
    Generate bid increment suggestions based on current bid.

    Args:
        current_bid (float): Current bid amount
        min_increment (float): Minimum bid increment
        count (int): Number of suggestions to generate
        factor (float): Factor to multiply each suggestion

    Returns:
        list: List of suggested bid amounts
    """
    if not current_bid:
        return []

    suggestions = []
    increment = max(min_increment, current_bid * 0.05)  # 5% of current bid or min_increment

    for i in range(count):
        suggestion = current_bid + increment * (factor ** i)
        # Round to nearest 100
        suggestion = round(suggestion / 100) * 100
        suggestions.append(suggestion)

    return suggestions


def get_property_valuation(property_obj, method='average', external_valuations=None):
    """
    Calculate property valuation based on different methods.

    Args:
        property_obj: Property object
        method (str): Valuation method ('average', 'max', 'min')
        external_valuations (list): List of external valuation amounts

    Returns:
        float: Property valuation amount
    """
    if not property_obj:
        return 0

    # Use market value if available
    if property_obj.market_value:
        return property_obj.market_value

    # Collect valuations including external ones
    valuations = []

    # Add auction values if available
    for auction in property_obj.auctions.filter(status__in=['completed', 'ended']):
        if auction.current_bid:
            valuations.append(auction.current_bid)

    # Add external valuations if provided
    if external_valuations:
        valuations.extend(external_valuations)

    # Calculate based on method
    if not valuations:
        return 0

    if method == 'average':
        return sum(valuations) / len(valuations)
    elif method == 'max':
        return max(valuations)
    elif method == 'min':
        return min(valuations)
    else:
        return sum(valuations) / len(valuations)  # Default to average


# -------------------------------------------------------------------------
# Role and Permission Utilities
# -------------------------------------------------------------------------

def get_user_role_display(user):
    """
    Get displayable role names for a user.

    Args:
        user: User object

    Returns:
        list: List of role display names
    """
    if not user or not hasattr(user, 'roles'):
        return []

    return [role.get_name_display() for role in user.roles.all()]


def get_user_permissions(user):
    """
    Get all permissions for a user based on their roles.

    Args:
        user: User object

    Returns:
        dict: Dictionary of permissions
    """
    if not user or not hasattr(user, 'roles'):
        return {}

    permissions = {}

    # Combine permissions from all roles
    for role in user.roles.all():
        role_permissions = role.default_permissions
        for perm_name, perm_value in role_permissions.items():
            # If permission already exists, set it to True if any role has it as True
            permissions[perm_name] = permissions.get(perm_name, False) or perm_value

    return permissions


def check_user_permission(user, permission_name):
    """
    Check if a user has a specific permission.

    Args:
        user: User object
        permission_name (str): Name of the permission to check

    Returns:
        bool: True if user has the permission
    """
    # Admin users have all permissions
    if user.has_role(Role.ADMIN):
        return True

    # Check user permissions from roles
    permissions = get_user_permissions(user)
    return permissions.get(permission_name, False)
