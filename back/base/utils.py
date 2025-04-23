import os
import uuid
import time
import random
import string
import hashlib
from typing import Union, List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from PIL import Image
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.db.models import Avg, Max, Min, Q
from .models import RoleChoices

# -------------------------------------------------------------------------
# File and Image Handling Utilities
# -------------------------------------------------------------------------

def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename while preserving the original extension.

    Args:
        original_filename: The original filename

    Returns:
        A unique filename with the same extension
    """
    ext = os.path.splitext(original_filename)[1].lower() if '.' in original_filename else ''
    unique_name = f"{uuid.uuid4()}{ext}"
    return unique_name


def create_thumbnail(image_file, size: Tuple[int, int] = (200, 200),
                    format: str = 'JPEG', quality: int = 85) -> Optional[ContentFile]:
    """
    Create a thumbnail from an image file.

    Args:
        image_file: Django UploadedFile or path to image
        size: Thumbnail dimensions (width, height)
        format: Image format for the thumbnail
        quality: Compression quality (1-100)

    Returns:
        Django ContentFile with the thumbnail or None if failed
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


def process_image_metadata(image_file) -> Dict[str, Any]:
    """
    Extract metadata from image file for storage.

    Args:
        image_file: Django UploadedFile or path to image

    Returns:
        Dictionary with image metadata (width, height, format, file_size)
    """
    if not image_file:
        return {}

    try:
        img = Image.open(image_file)
        metadata = {
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'file_size': get_file_size_in_kb(image_file),
            'aspect_ratio': round(img.width / img.height, 2) if img.height > 0 else 0
        }

        # Extract EXIF data if available
        exif_data = {}
        if hasattr(img, '_getexif') and img._getexif():
            exif = img._getexif()
            if exif:
                from PIL.ExifTags import TAGS
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

            metadata['exif'] = exif_data

        return metadata
    except Exception as e:
        print(f"Error extracting image metadata: {str(e)}")
        return {'error': str(e)}


def get_file_size_in_kb(file_obj) -> int:
    """
    Get file size in KB from a file object.

    Args:
        file_obj: Django File or UploadedFile object

    Returns:
        File size in KB or 0 if file doesn't exist
    """
    if not file_obj:
        return 0
    try:
        return file_obj.size // 1024
    except (AttributeError, IOError):
        return 0


def validate_image_file(file_obj, max_size_mb: int = 5,
                        allowed_extensions: List[str] = None) -> bool:
    """
    Validate an image file for size and format.

    Args:
        file_obj: Django File or UploadedFile object
        max_size_mb: Maximum file size in MB
        allowed_extensions: List of allowed file extensions

    Raises:
        ValidationError: If validation fails

    Returns:
        True if validation passes
    """
    if not file_obj:
        return True

    if allowed_extensions is None:
        allowed_extensions = ['jpg', 'jpeg', 'png', 'webp', 'gif']

    max_size_bytes = max_size_mb * 1024 * 1024
    if file_obj.size > max_size_bytes:
        raise ValidationError(_('File size exceeds the limit (%(max_size)s MB).') % {'max_size': max_size_mb})

    ext = os.path.splitext(file_obj.name)[1].lower().lstrip('.')
    if ext not in allowed_extensions:
        raise ValidationError(_('Unsupported file type. Supported types: %(ext_list)s.') % {'ext_list': ', '.join(allowed_extensions)})

    return True


def calculate_file_hash(file_obj, algorithm: str = 'sha256') -> Optional[str]:
    """
    Calculate a hash of a file for verification purposes.

    Args:
        file_obj: Django File or UploadedFile object
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)

    Returns:
        Hexadecimal string of the file hash or None if failed
    """
    if not file_obj:
        return None

    try:
        hasher = hashlib.new(algorithm)
        for chunk in file_obj.chunks(1024 * 1024):  # 1MB chunks
            hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error calculating file hash: {str(e)}")
        return None


# -------------------------------------------------------------------------
# String and Text Utilities
# -------------------------------------------------------------------------

def generate_random_code(length: int = 6, chars: str = string.digits) -> str:
    """
    Generate a random code of specified length.

    Args:
        length: Length of the code
        chars: Characters to use for the code

    Returns:
        Random code
    """
    return ''.join(random.choice(chars) for _ in range(length))


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Length of the token

    Returns:
        Secure random token string
    """
    import secrets
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_reference_number(prefix: str, year: Optional[int] = None,
                             length: int = 8, separator: str = '-') -> str:
    """
    Generate a reference number for properties, auctions, contracts.

    Args:
        prefix: Prefix for the reference number (e.g., 'PROP', 'AUC')
        year: Year to include (defaults to current year)
        length: Length of the random part
        separator: Separator character

    Returns:
        Reference number in format PREFIX-YEAR-RANDOM
    """
    if year is None:
        year = datetime.now().year

    random_part = ''.join(random.choice(string.digits) for _ in range(length))
    return f"{prefix}{separator}{year}{separator}{random_part}"


def generate_slug(text: str, model_class, max_length: int = 255) -> str:
    """
    Generate a unique slug for a model.

    Args:
        text: Text to slugify
        model_class: Django model class
        max_length: Maximum slug length

    Returns:
        Unique slug
    """
    original_slug = slugify(text)[:max_length]
    if not original_slug:
        # If slugify produces an empty string, use a timestamp
        original_slug = f"item-{int(time.time())}"[:max_length]

    slug = original_slug
    counter = 1
    while model_class.objects.filter(slug=slug).exists():
        suffix = f"-{counter}"
        slug = f"{original_slug[:max_length - len(suffix)]}{suffix}"
        counter += 1
    return slug


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        html_content: HTML content to sanitize

    Returns:
        Sanitized HTML content
    """
    try:
        import bleach
        allowed_tags = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'br', 'ul', 'ol', 'li',
                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'blockquote', 'img',
                        'pre', 'code', 'span', 'div', 'table', 'thead', 'tbody', 'tr',
                        'th', 'td']
        allowed_attrs = {
            'a': ['href', 'title', 'target', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            '*': ['class', 'style', 'id', 'dir']
        }
        return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    except ImportError:
        # Basic sanitation if bleach is not available
        replacements = [
            ('<script', '&lt;script'),
            ('javascript:', 'disabled-javascript:'),
            ('onerror=', 'data-onerror='),
            ('onclick=', 'data-onclick='),
            ('onload=', 'data-onload='),
            ('onmouseover=', 'data-onmouseover=')
        ]
        for old, new in replacements:
            html_content = html_content.replace(old, new)
        return html_content


def truncate_text(text: str, length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to a specified length with ellipsis.

    Args:
        text: Text to truncate
        length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + suffix


# -------------------------------------------------------------------------
# Date and Time Utilities
# -------------------------------------------------------------------------

def format_datetime(dt, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object as a string.

    Args:
        dt: Datetime object
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    if not dt:
        return ""
    return dt.strftime(format_str)


def format_arabic_date(dt) -> str:
    """
    Format a date in Arabic style (Day Month Year).

    Args:
        dt: Datetime object

    Returns:
        Arabic formatted date string
    """
    if not dt:
        return ""

    # Arabic month names
    ar_months = [
        "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
        "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
    ]

    return f"{dt.day} {ar_months[dt.month-1]} {dt.year}"


def get_time_remaining(end_date) -> Dict[str, Union[int, float]]:
    """
    Calculate time remaining until end_date.

    Args:
        end_date: End date

    Returns:
        Dict with time remaining in days, hours, minutes, seconds and total_seconds
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


def is_date_in_range(date, start_date=None, end_date=None) -> bool:
    """
    Check if a date is within a range.

    Args:
        date: Date to check
        start_date: Start date of range
        end_date: End date of range

    Returns:
        True if date is in range
    """
    if not date:
        return False
    if start_date and date < start_date:
        return False
    if end_date and date > end_date:
        return False
    return True


def generate_date_ranges(start_date, end_date, interval_days: int = 30) -> List[Dict[str, datetime]]:
    """
    Generate a list of date ranges between start and end dates.

    Args:
        start_date: Start date
        end_date: End date
        interval_days: Interval between ranges in days

    Returns:
        List of dictionaries with from_date and to_date
    """
    if not start_date or not end_date or start_date >= end_date:
        return []

    ranges = []
    current = start_date

    while current < end_date:
        range_end = min(current + timedelta(days=interval_days), end_date)
        ranges.append({
            'from_date': current,
            'to_date': range_end
        })
        current = range_end + timedelta(days=1)

    return ranges


# -------------------------------------------------------------------------
# Financial Utilities
# -------------------------------------------------------------------------

def calculate_fee(amount, percentage, round_to: int = 2) -> Decimal:
    """
    Calculate a fee based on a percentage.

    Args:
        amount: Base amount
        percentage: Fee percentage
        round_to: Number of decimal places to round to

    Returns:
        Fee amount
    """
    if not amount or not percentage:
        return Decimal('0.00')
    amount_decimal = Decimal(str(amount))
    percentage_decimal = Decimal(str(percentage))
    fee = (amount_decimal * percentage_decimal) / Decimal('100')
    return fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def format_currency(amount, currency: str = 'SAR', locale: str = 'ar_SA') -> str:
    """
    Format a currency amount according to locale.

    Args:
        amount: Amount to format
        currency: Currency code
        locale: Locale to use for formatting

    Returns:
        Formatted currency string
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


def calculate_installments(total_amount, payment_count: int,
                          interval_days: int = 30) -> List[Dict[str, Any]]:
    """
    Calculate installment amounts and dates.

    Args:
        total_amount: Total amount to pay
        payment_count: Number of installments
        interval_days: Interval between payments in days

    Returns:
        List of dictionaries with amount and due_date
    """
    if not total_amount or payment_count < 1:
        return []
    total_amount = Decimal(str(total_amount))
    payment_amount = (total_amount / payment_count).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    installments = []
    start_date = timezone.now()
    for i in range(payment_count):
        due_date = start_date + timedelta(days=interval_days * (i + 1))
        if i == payment_count - 1:
            prev_sum = payment_amount * (payment_count - 1)
            amount = (total_amount - prev_sum).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            amount = payment_amount
        installments.append({
            'number': i + 1,
            'amount': amount,
            'due_date': due_date,
            'percentage': ((amount / total_amount) * 100).quantize(Decimal('0.01'))
        })
    return installments


def calculate_mortgage_payments(loan_amount, interest_rate: Decimal,
                              term_years: int, payment_frequency: str = 'monthly') -> Dict[str, Any]:
    """
    Calculate mortgage payment details.

    Args:
        loan_amount: Principal loan amount
        interest_rate: Annual interest rate (percentage)
        term_years: Loan term in years
        payment_frequency: Payment frequency (monthly, quarterly, annually)

    Returns:
        Dictionary with payment details including monthly payment, total interest, total cost
    """
    loan_amount = Decimal(str(loan_amount))
    interest_rate = Decimal(str(interest_rate))

    # Convert annual rate to decimal and adjust for payment frequency
    if payment_frequency == 'monthly':
        periods = term_years * 12
        rate_per_period = interest_rate / 100 / 12
    elif payment_frequency == 'quarterly':
        periods = term_years * 4
        rate_per_period = interest_rate / 100 / 4
    elif payment_frequency == 'annually':
        periods = term_years
        rate_per_period = interest_rate / 100
    else:
        periods = term_years * 12
        rate_per_period = interest_rate / 100 / 12

    # Calculate payment using mortgage formula
    if rate_per_period == 0:
        payment = loan_amount / periods
    else:
        payment = loan_amount * (rate_per_period * (1 + rate_per_period) ** periods) / ((1 + rate_per_period) ** periods - 1)

    payment = payment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_paid = payment * periods
    total_interest = total_paid - loan_amount

    return {
        'payment_amount': payment,
        'payment_frequency': payment_frequency,
        'number_of_payments': periods,
        'total_interest': total_interest.quantize(Decimal('0.01')),
        'total_cost': total_paid.quantize(Decimal('0.01')),
        'interest_rate': interest_rate
    }


# -------------------------------------------------------------------------
# Auction and Property Utilities
# -------------------------------------------------------------------------

def check_auction_status(auction) -> str:
    """
    Check and update auction status based on dates.

    Args:
        auction: Auction object

    Returns:
        Current auction status

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


def extend_auction_time(auction, extension_minutes: int = 10) -> bool:
    """
    Extend auction end time when bids are placed near the end.

    Args:
        auction: Auction object
        extension_minutes: Minutes to extend auction by

    Returns:
        True if auction was extended, False otherwise
    """
    if not auction or auction.status != 'live':
        return False

    now = timezone.now()
    remaining = (auction.end_date - now).total_seconds() / 60

    # If less than 5 minutes remaining, extend the auction
    if 0 < remaining < 5:
        auction.end_date = auction.end_date + timedelta(minutes=extension_minutes)
        auction.save(update_fields=['end_date'])
        return True

    return False


def get_bid_increment_suggestions(current_bid, min_increment=100,
                                 count: int = 3, factor: float = 1.5) -> List[Decimal]:
    """
    Generate bid increment suggestions based on current bid.

    Args:
        current_bid: Current bid amount
        min_increment: Minimum bid increment
        count: Number of suggestions to generate
        factor: Factor to multiply each suggestion

    Returns:
        List of Decimal suggested bid amounts
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

    # Calculate base increment (either min_increment or 5% of current bid, whichever is higher)
    increment = max(min_increment, current_bid * Decimal('0.05'))

    for i in range(count):
        suggestion = current_bid + increment * (factor ** i)
        suggestions.append(suggestion.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    return suggestions


def get_property_valuation(property_obj, method: str = 'average',
                          external_valuations: List[Union[Decimal, float, int]] = None) -> Decimal:
    """
    Calculate property valuation based on different methods.

    Args:
        property_obj: Property object
        method: Valuation method ('average', 'max', 'min')
        external_valuations: List of external valuation amounts

    Returns:
        Property valuation amount
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
        return (sum(valuations) / len(valuations)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    elif method == 'max':
        return max(valuations)
    elif method == 'min':
        return min(valuations)
    return (sum(valuations) / len(valuations)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_similar_properties(property_obj, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Find similar properties based on location, type, and characteristics.

    Args:
        property_obj: Property object
        limit: Maximum number of similar properties to return

    Returns:
        List of similar property dictionaries with similarity scores
    """
    from django.db.models import F

    if not property_obj or not hasattr(property_obj, 'property_type'):
        return []

    # Get the Property model class dynamically
    Property = property_obj.__class__

    # Base query for properties of same type excluding the current property
    similar_props = Property.objects.filter(
        property_type=property_obj.property_type,
        is_published=True
    ).exclude(id=property_obj.id)

    # Narrow by location if available
    if property_obj.city:
        similar_props = similar_props.filter(city=property_obj.city)

    # Narrow by size similarity if available
    if property_obj.size_sqm:
        similar_props = similar_props.filter(
            size_sqm__gte=property_obj.size_sqm * Decimal('0.7'),
            size_sqm__lte=property_obj.size_sqm * Decimal('1.3')
        )

    # Narrow by room counts if available
    if property_obj.bedrooms:
        similar_props = similar_props.filter(
            Q(bedrooms=property_obj.bedrooms) |
            Q(bedrooms=property_obj.bedrooms+1) |
            Q(bedrooms=property_obj.bedrooms-1)
        )

    # Score and sort the properties
    result = []
    for prop in similar_props[:20]:  # Get top 20 for scoring
        score = 100  # Base score

        # Reduce score based on price difference
        if property_obj.market_value and prop.market_value:
            price_diff_pct = abs(prop.market_value - property_obj.market_value) / property_obj.market_value
            score -= min(40, int(price_diff_pct * 100))

        # Reduce score based on size difference
        if property_obj.size_sqm and prop.size_sqm:
            size_diff_pct = abs(prop.size_sqm - property_obj.size_sqm) / property_obj.size_sqm
            score -= min(30, int(size_diff_pct * 100))

        # Add to results if score is reasonable
        if score > 50:
            result.append({
                'id': prop.id,
                'title': prop.title,
                'property_type': prop.property_type,
                'property_type_display': prop.get_property_type_display(),
                'market_value': prop.market_value,
                'size_sqm': prop.size_sqm,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'city': prop.city,
                'address': prop.address,
                'cover_image_url': prop.cover_image.url if hasattr(prop, 'cover_image') and prop.cover_image else None,
                'similarity_score': score
            })

    # Sort by similarity score and limit results
    result.sort(key=lambda x: x['similarity_score'], reverse=True)
    return result[:limit]


# -------------------------------------------------------------------------
# Permission Utilities
# -------------------------------------------------------------------------

def get_user_permissions(user):
    """
    Get all permissions for a user based on attributes and Django permissions.

    Args:
        user: User object

    Returns:
        Set of permission strings
    """
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return set()

    permissions = set()

    # Admin users have all permissions
    if user.is_staff or user.is_superuser:
        permissions.update([
            'manage_properties',
            'manage_auctions',
            'manage_bids',
            'verify_documents',
            'manage_users',
            'approve_contracts',
            'view_all_bids',
            'manage_notifications',
            'create_property',
            'create_auction',
            'place_bids',
            'send_messages',
        ])
        return permissions

    # Attribute-based permissions
    if hasattr(user, 'is_verified') and user.is_verified:
        permissions.update([
            'place_bids',
            'send_messages'
        ])

    # Basic permissions for authenticated users
    permissions.add('view_public_resources')

    # Property owner permissions
    if hasattr(user, 'owned_properties') and user.owned_properties.exists():
        permissions.update([
            'manage_owned_properties',
            'create_property',
            'create_auction'
        ])

    # Add Django permission system permissions
    if hasattr(user, 'get_all_permissions'):
        for perm in user.get_all_permissions():
            permissions.add(perm.split('.')[-1])

    return permissions

def check_user_permission(user, permission_name):
    """
    Check if user has a specific permission.

    Args:
        user: User object
        permission_name: Permission to check

    Returns:
        True if user has the permission
    """
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False

    # Admin users have all permissions
    if user.is_staff or user.is_superuser:
        return True

    # Check explicit permissions
    return permission_name in get_user_permissions(user)

# -------------------------------------------------------------------------
# Arabic Slug Utility
# -------------------------------------------------------------------------

def arabic_slugify(text):
    """
    Generate a URL-friendly slug that preserves Arabic characters.

    Args:
        text: The text to slugify

    Returns:
        A URL-friendly slug with Arabic characters preserved
    """
    import re

    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text.strip())
    # Remove special characters that are problematic in URLs
    text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\w\-]', '', text)
    # Convert to lowercase (for any Latin characters)
    text = text.lower()
    # Ensure no double hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')

    # If slug is empty after processing Arabic text, use default slugify
    if not text:
        return slugify(text)

    return text
