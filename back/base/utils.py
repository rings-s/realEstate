import os
import uuid
import time
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
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
        ContentFile: Django ContentFile with the thumbnail or None if failed
    """
    if not image_file:
        return None

    try:
        img = Image.open(image_file)
        if img.mode not in ('L', 'RGB', 'RGBA'):
            img = img.convert('RGB')
        img.thumbnail(size, Image.LANCZOS)
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

    max_size_bytes = max_size_mb * 1024 * 1024
    if file_obj.size > max_size_bytes:
        raise ValidationError(_('حجم الملف يتجاوز الحد المسموح به (%(max_size)s ميجابايت).') % {'max_size': max_size_mb})

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
    counter = 1
    while model_class.objects.filter(slug=slug).exists():
        suffix = f"-{counter}"
        slug = f"{original_slug[:max_length - len(suffix)]}{suffix}"
        counter += 1
    return slug

def sanitize_html(html_content):
    """
    Sanitize HTML content to prevent XSS attacks.

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
        replacements = [
            ('<script', '<script'),
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
        return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0, 'total_seconds': 0}

    now = timezone.now()
    if end_date <= now:
        return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0, 'total_seconds': 0}

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
        amount (Decimal/float): Base amount
        percentage (Decimal/float): Fee percentage

    Returns:
        Decimal: Fee amount
    """
    if not amount or not percentage:
        return Decimal('0.00')
    return (Decimal(str(amount)) * Decimal(str(percentage))) / Decimal('100').quantize(Decimal('0.01'))

def format_currency(amount, currency='SAR', locale='ar_SA'):
    """
    Format a currency amount according to locale.

    Args:
        amount (Decimal/float): Amount to format
        currency (str): Currency code
        locale (str): Locale to use for formatting

    Returns:
        str: Formatted currency string
    """
    if amount is None:
        return ""
    amount = Decimal(str(amount))
    try:
        import locale as locale_module
        locale_module.setlocale(locale_module.LC_ALL, locale)
        return locale_module.currency(amount, symbol=currency, grouping=True)
    except (ImportError, locale_module.Error):
        if locale.startswith('ar'):
            return f"{amount:,.2f} {currency}"
        return f"{currency} {amount:,.2f}"

def calculate_installments(total_amount, payment_count, interval_days=30):
    """
    Calculate installment amounts and dates.

    Args:
        total_amount (Decimal/float): Total amount to pay
        payment_count (int): Number of installments
        interval_days (int): Interval between payments in days

    Returns:
        list: List of dictionaries with amount and due_date
    """
    if not total_amount or payment_count < 1:
        return []
    total_amount = Decimal(str(total_amount))
    payment_amount = (total_amount / payment_count).quantize(Decimal('0.01'))
    installments = []
    start_date = timezone.now()
    for i in range(payment_count):
        due_date = start_date + timedelta(days=interval_days * (i + 1))
        if i == payment_count - 1:
            prev_sum = payment_amount * (payment_count - 1)
            amount = (total_amount - prev_sum).quantize(Decimal('0.01'))
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

    Raises:
        ValueError: If auction is None
    """
    if auction is None:
        raise ValueError(_('Auction object cannot be None'))
    now = timezone.now()
    if auction.status in ['completed', 'cancelled']:
        return auction.status
    if auction.start_date > now:
        new_status = 'scheduled'
    elif auction.end_date < now:
        new_status = 'ended'
    else:
        new_status = 'live'
    if new_status != auction.status:
        auction.status = new_status
        auction.save(update_fields=['status'])
    return auction.status

def get_bid_increment_suggestions(current_bid, min_increment=100, count=3, factor=1.5):
    """
    Generate bid increment suggestions based on current bid.

    Args:
        current_bid (Decimal/float): Current bid amount
        min_increment (Decimal/float): Minimum bid increment
        count (int): Number of suggestions to generate
        factor (float): Factor to multiply each suggestion

    Returns:
        list: List of Decimal suggested bid amounts
    """
    if not current_bid or not min_increment:
        return []
    try:
        current_bid = Decimal(str(current_bid))
        min_increment = Decimal(str(min_increment))
        factor = Decimal(str(factor))
    except (ValueError, TypeError):
        return []
    suggestions = []
    increment = max(min_increment, current_bid * Decimal('0.05'))
    for i in range(count):
        suggestion = current_bid + increment * (factor ** i)
        suggestions.append(suggestion.quantize(Decimal('0.01')))
    return suggestions

def get_property_valuation(property_obj, method='average', external_valuations=None):
    """
    Calculate property valuation based on different methods.

    Args:
        property_obj: Property object
        method (str): Valuation method ('average', 'max', 'min')
        external_valuations (list): List of external valuation amounts

    Returns:
        Decimal: Property valuation amount
    """
    if not property_obj:
        return Decimal('0.00')
    if property_obj.market_value:
        return Decimal(str(property_obj.market_value))
    valuations = []
    for auction in property_obj.auctions.filter(status__in=['completed', 'ended']):
        if auction.current_bid:
            valuations.append(Decimal(str(auction.current_bid)))
    if external_valuations:
        valuations.extend(Decimal(str(v)) for v in external_valuations if v)
    if not valuations:
        return Decimal('0.00')
    if method == 'average':
        return (sum(valuations) / len(valuations)).quantize(Decimal('0.01'))
    elif method == 'max':
        return max(valuations)
    elif method == 'min':
        return min(valuations)
    return (sum(valuations) / len(valuations)).quantize(Decimal('0.01'))

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
        set: Set of permission strings
    """
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return set()
    permissions = set()
    if user.has_role(Role.ADMIN):
        permissions.update(['can_create_property', 'can_create_auction'])
        return permissions
    for role in user.roles.all():
        if role.name in ['seller', 'owner']:
            permissions.update(['can_create_property', 'can_create_auction'])
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
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    if user.has_role(Role.ADMIN):
        return True
    return permission_name in get_user_permissions(user)
