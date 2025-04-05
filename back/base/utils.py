"""
Optimized utilities for Real Estate Auction Platform.
"""

import logging
import uuid
import json
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Count, Sum, F, QuerySet
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

# Configure logger
logger = logging.getLogger(__name__)
User = get_user_model()

# ============================================================================
# Response Formatting
# ============================================================================

def create_response(
    data: Any = None,
    message: str = None,
    error: str = None,
    error_code: str = None,
    status_code: int = status.HTTP_200_OK
) -> Response:
    """Create a standardized API response."""
    response_data = {"status": "success" if not error else "error"}

    if message:
        response_data["message"] = message

    if data is not None:
        response_data["data"] = data

    if error:
        response_data["error"] = error

    if error_code:
        response_data["error_code"] = error_code

    return Response(response_data, status=status_code)


def paginate_queryset(queryset, request, view, serializer_class):
    """Paginate a queryset and return serialized data."""
    paginator = view.pagination_class()
    page = paginator.paginate_queryset(queryset, request, view=view)

    if page is not None:
        serializer = serializer_class(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    serializer = serializer_class(queryset, many=True, context={'request': request})
    return Response(serializer.data)


# ============================================================================
# Validation Utilities
# ============================================================================

def validate_status_transition(
    original_status: str,
    new_status: str,
    allowed_transitions: Dict[str, List[str]]
) -> bool:
    """Validate if a status transition is allowed."""
    if original_status == new_status:
        return True

    if original_status not in allowed_transitions:
        raise ValidationError(_(f"Invalid original status: {original_status}"))

    if new_status not in allowed_transitions[original_status]:
        allowed = ", ".join(allowed_transitions[original_status])
        raise ValidationError(
            _(f"Cannot transition from '{original_status}' to '{new_status}'. "
              f"Allowed transitions: {allowed}")
        )

    return True



# ============================================================================
# Slug and Unique ID Generation
# ============================================================================

def arabic_slugify(text):
    """
    Custom slugify function that preserves Arabic characters.
    Replaces spaces and special characters with hyphens.
    """
    if not text:
        return ""
    # Replace special characters with empty string
    import re
    text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\w\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text).strip('-')
    # Remove repeated hyphens
    text = re.sub(r'-+', '-', text)
    return text


def generate_unique_slug(title, model_class, slug_field='slug', max_retries=5):
    """Generate a unique slug for a model instance."""
    base_slug = arabic_slugify(title)
    if not base_slug:
        base_slug = str(uuid.uuid4())[:8]

    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')

    for attempt in range(max_retries):
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        unique_slug = f"{base_slug}-{timestamp}-{random_suffix}"

        if not model_class.objects.filter(**{slug_field: unique_slug}).exists():
            return unique_slug

    raise ValueError(f"Unable to generate a unique slug after {max_retries} attempts")


def generate_reference_number(prefix: str, model_class, ref_field: str) -> str:
    """Generate a unique reference number (e.g., for contracts, payments)."""
    date_part = timezone.now().strftime('%Y%m%d')

    for _ in range(5):
        random_part = ''.join([str(uuid.uuid4().hex)[:6].upper()])
        reference = f"{prefix}-{date_part}-{random_part}"

        if not model_class.objects.filter(**{ref_field: reference}).exists():
            return reference

    # Fallback to timestamp
    timestamp = int(timezone.now().timestamp())
    return f"{prefix}-{date_part}-{timestamp}"


# ============================================================================
# Media Handling
# ============================================================================

class MediaHandler:
    """
    Central media handling class for processing uploads across different models.
    Provides standardized methods for validating, saving, and managing media files.
    """
    # File type configurations
    ALLOWED_EXTENSIONS = {
        'image': ['jpg', 'jpeg', 'png', 'webp', 'gif'],
        'document': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'xls', 'xlsx', 'csv'],
        'video': ['mp4', 'webm', 'mov', 'avi']
    }

    # Maximum file sizes in bytes
    MAX_SIZES = {
        'image': 5 * 1024 * 1024,    # 5MB
        'document': 10 * 1024 * 1024, # 10MB
        'video': 50 * 1024 * 1024    # 50MB
    }

    @classmethod
    def validate_file(cls, file, file_type='image'):
        """
        Validate file size and extension based on file type.
        Returns (valid, error_message)
        """
        if not file:
            return False, _("No file provided")

        # Validate file extension
        extension = file.name.split('.')[-1].lower()
        allowed_exts = cls.ALLOWED_EXTENSIONS.get(file_type, [])
        max_size = cls.MAX_SIZES.get(file_type, 5 * 1024 * 1024)

        if not allowed_exts:
            return False, _("Unsupported file type")

        if extension not in allowed_exts:
            return False, _(f"Invalid file format. Allowed formats: {', '.join(allowed_exts)}")

        if file.size > max_size:
            max_size_mb = max_size // (1024 * 1024)
            return False, _(f"File too large. Maximum size: {max_size_mb}MB")

        return True, None

    @classmethod
    def save_file(cls, file, entity_type, entity_id, file_type='image'):
        """
        Save a file and return the file path and metadata.
        entity_type: 'property', 'auction', 'document', etc.
        """
        # Validate file
        is_valid, error = cls.validate_file(file, file_type)
        if not is_valid:
            raise ValueError(error)

        # Create unique filename
        extension = file.name.split('.')[-1].lower()
        filename = f"{uuid.uuid4().hex}.{extension}"

        # Create path by date
        date_path = timezone.now().strftime('%Y/%m/%d')

        # Final path: media/entity_type/file_type/date/entity_id/filename
        relative_path = f"media/{entity_type}/{file_type}/{date_path}/{entity_id}/{filename}"

        # Save file
        file_path = default_storage.save(relative_path, ContentFile(file.read()))
        file_url = default_storage.url(file_path)

        # Build file info
        file_info = {
            'id': str(uuid.uuid4()),  # Unique ID for the file
            'url': file_url,
            'path': file_path,
            'name': file.name,
            'size': file.size,
            'content_type': file.content_type,
            'extension': extension,
            'uploaded_at': timezone.now().isoformat(),
            'is_primary': False  # Default, can be updated later
        }

        return file_info

    @classmethod
    def process_property_images(cls, property_obj, files):
        """
        Process multiple image uploads for a property.
        Returns a list of processed image data.
        """
        if not property_obj or not property_obj.pk:
            raise ValueError(_("Property must be saved before uploading images"))

        current_images = property_obj.get_json_field('images', [])
        new_images = []

        for file in files:
            try:
                # Validate and save each image
                file_info = cls.save_file(file, 'property', property_obj.pk, 'image')

                # If this is the first image, mark it as primary
                if not current_images and not new_images:
                    file_info['is_primary'] = True

                new_images.append(file_info)
            except Exception as e:
                logger.error(f"Error processing image {file.name}: {str(e)}")

        # Combine with existing images
        updated_images = current_images + new_images

        # Update the property
        property_obj.set_json_field('images', updated_images)
        property_obj.save(update_fields=['images', 'updated_at'])

        return new_images

    @classmethod
    def set_primary_image(cls, property_obj, image_index):
        """Set the primary image for a property by index."""
        images = property_obj.get_json_field('images', [])

        if not images or image_index >= len(images):
            raise ValueError(_("Invalid image index"))

        # Reset all primary flags
        for img in images:
            img['is_primary'] = False

        # Set the selected image as primary
        images[image_index]['is_primary'] = True

        # Update the property
        property_obj.set_json_field('images', images)
        property_obj.save(update_fields=['images', 'updated_at'])

        return images[image_index]

    @classmethod
    def delete_image(cls, property_obj, image_index):
        """Delete an image by index."""
        images = property_obj.get_json_field('images', [])

        if not images or image_index >= len(images):
            raise ValueError(_("Invalid image index"))

        # Get the image to delete
        image = images[image_index]

        # Check if we're deleting the primary image
        was_primary = image.get('is_primary', False)

        # Remove from storage if possible
        try:
            if 'path' in image and default_storage.exists(image['path']):
                default_storage.delete(image['path'])
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")

        # Remove from list
        deleted_image = images.pop(image_index)

        # If we deleted the primary image and have other images, set a new primary
        if was_primary and images:
            images[0]['is_primary'] = True

        # Update the property
        property_obj.set_json_field('images', images)
        property_obj.save(update_fields=['images', 'updated_at'])

        return deleted_image

    @classmethod
    def process_document_files(cls, document_obj, files):
        """Process document file uploads."""
        if not document_obj or not document_obj.pk:
            raise ValueError(_("Document must be saved before uploading files"))

        current_files = document_obj.get_json_field('files', [])
        new_files = []

        for file in files:
            try:
                # Validate and save document
                file_info = cls.save_file(file, 'document', document_obj.pk, 'document')
                new_files.append(file_info)
            except Exception as e:
                logger.error(f"Error processing document {file.name}: {str(e)}")

        # Combine with existing documents
        updated_files = current_files + new_files

        # Update the document object
        document_obj.set_json_field('files', updated_files)
        document_obj.save(update_fields=['files', 'updated_at'])

        return new_files

    @classmethod
    def process_auction_images(cls, auction_obj, files):
        """Process multiple image uploads for an auction."""
        if not auction_obj or not auction_obj.pk:
            raise ValueError(_("Auction must be saved before uploading images"))

        current_images = auction_obj.get_json_field('images', [])
        new_images = []

        for file in files:
            try:
                file_info = cls.save_file(file, 'auction', auction_obj.pk, 'image')

                # If this is the first image, mark it as primary
                if not current_images and not new_images:
                    file_info['is_primary'] = True

                new_images.append(file_info)
            except Exception as e:
                logger.error(f"Error processing auction image {file.name}: {str(e)}")

        updated_images = current_images + new_images
        auction_obj.set_json_field('images', updated_images)
        auction_obj.save(update_fields=['images', 'updated_at'])

        return new_images
