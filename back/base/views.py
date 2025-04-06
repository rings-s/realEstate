import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import F, Q, Exists, OuterRef, Subquery
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied

from .models import (
    Property, Auction, Bid, Document, Contract, Payment, Transaction,
    PropertyView, MessageThread, Message, ThreadParticipant, Notification
)

from .serializers import (
    PropertySerializer, AuctionSerializer, BidSerializer, DocumentSerializer,
    ContractSerializer, PaymentSerializer, TransactionSerializer,
    PropertyViewSerializer, MessageThreadSerializer, MessageSerializer,
    ThreadParticipantSerializer, NotificationSerializer
)
from .permissions import (
    IsPropertyOwner, IsAuctionCreator, IsSellerPermission, IsBuyerPermission,
    IsInspectorPermission, IsLegalPermission, IsAgentPermission, IsAppraiserPermission
)
from .decorators import (
    debug_request, handle_exceptions, cache_view, timer,
    CACHE_SHORT, CACHE_MEDIUM, CACHE_LONG
)
from .utils import MediaHandler, create_response
from accounts.models import Role

logger = logging.getLogger(__name__)



# BaseAPIView with fixed permission_denied method
class BaseAPIView(APIView):
    """Base API view with common functionality and error handling"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination

    # Define permission map for different HTTP methods
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAdminUser],
        'put': [permissions.IsAdminUser],
        'patch': [permissions.IsAdminUser],
        'delete': [permissions.IsAdminUser],
    }

    @handle_exceptions
    def dispatch(self, request, *args, **kwargs):
        """Apply exception handling to all methods"""
        return super().dispatch(request, *args, **kwargs)

    def get_permissions(self):
        """Get permissions based on request method"""
        method = self.request.method.lower()
        if method in self.action_permission_map:
            return [permission() for permission in self.action_permission_map[method]]
        return [permission() for permission in self.permission_classes]

    def paginate_queryset(self, queryset):
        """Paginate a queryset"""
        if not hasattr(self, '_paginator'):
            self._paginator = self.pagination_class()
        return self._paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """Return a paginated response"""
        return self._paginator.get_paginated_response(data)

    # Shorthand response methods
    def error_response(self, error, error_code=None, status_code=status.HTTP_400_BAD_REQUEST):
        return create_response(error=error, error_code=error_code, status_code=status_code)

    def success_response(self, data=None, message=None, status_code=status.HTTP_200_OK):
        return create_response(data=data, message=message, status_code=status_code)

    def not_found(self, message="Resource not found"):
        return self.error_response(error=message, error_code="not_found", status_code=status.HTTP_404_NOT_FOUND)

    # FIXED METHOD - Added request parameter and code parameter to match DRF's signature
    def permission_denied(self, request=None, message="Permission denied", code=None):
        """
        Override DRF's permission_denied method to use our response format.
        Matches Django REST Framework's method signature to avoid conflicts.
        """
        error_code = code or "permission_denied"
        return self.error_response(error=message, error_code=error_code, status_code=status.HTTP_403_FORBIDDEN)




# Base class for file uploads
class BaseUploadView(BaseAPIView):
    """
    Base class for handling file uploads.
    This should be subclassed for specific entity types.
    """
    permission_classes = [permissions.IsAuthenticated]

    # Configuration to be set by subclasses
    model_class = None
    file_field_name = 'files'
    allow_multiple = True
    allowed_extensions = []
    max_file_size = 5 * 1024 * 1024  # 5MB default

    def get_object(self, pk):
        """Get the object and verify permissions"""
        if not self.model_class:
            raise ValueError("model_class must be set in subclass")

        obj = get_object_or_404(self.model_class, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    @handle_exceptions
    @transaction.atomic
    def post(self, request, pk):
        """Upload files for an entity"""
        try:
            # Get entity and check permissions
            obj = self.get_object(pk)

            # Check if files were provided
            if self.file_field_name not in request.FILES:
                return self.error_response(
                    _('No files were provided'),
                    'no_files',
                    status.HTTP_400_BAD_REQUEST
                )

            # Get files
            files = request.FILES.getlist(self.file_field_name)

            # Check if multiple files are allowed
            if not self.allow_multiple and len(files) > 1:
                return self.error_response(
                    _('Only one file is allowed'),
                    'too_many_files',
                    status.HTTP_400_BAD_REQUEST
                )

            # Check for max files
            if len(files) > 10:  # Hardcoded limit for safety
                return self.error_response(
                    _('Too many files. Maximum is 10 files per upload.'),
                    'too_many_files',
                    status.HTTP_400_BAD_REQUEST
                )

            # Validate file extensions
            if self.allowed_extensions:
                for file in files:
                    ext = file.name.split('.')[-1].lower()
                    if ext not in self.allowed_extensions:
                        return self.error_response(
                            _('Invalid file type. Allowed types: {}').format(
                                ', '.join(self.allowed_extensions)
                            ),
                            'invalid_file_type',
                            status.HTTP_400_BAD_REQUEST
                        )

            # Validate file sizes
            for file in files:
                if file.size > self.max_file_size:
                    return self.error_response(
                        _('File too large. Maximum size is {} MB').format(
                            self.max_file_size / (1024 * 1024)
                        ),
                        'file_too_large',
                        status.HTTP_400_BAD_REQUEST
                    )

            # Process files based on model type
            if self.model_class.__name__ == 'Property' and self.file_field_name == 'images':
                new_files = MediaHandler.process_property_images(obj, files)
            elif self.model_class.__name__ == 'Auction' and self.file_field_name == 'images':
                new_files = MediaHandler.process_auction_images(obj, files)
            elif self.model_class.__name__ == 'Document' and self.file_field_name == 'files':
                new_files = MediaHandler.process_document_files(obj, files)
            elif hasattr(obj, 'get_json_field') and hasattr(obj, 'set_json_field'):
                # Generic handling for models with JsonFieldMixin
                current_files = obj.get_json_field(self.file_field_name, [])
                new_files = []

                for file in files:
                    file_info = MediaHandler.save_file(
                        file,
                        self.model_class.__name__.lower(),
                        obj.pk,
                        self.file_field_name
                    )
                    new_files.append(file_info)

                updated_files = current_files + new_files
                obj.set_json_field(self.file_field_name, updated_files)
                obj.save(update_fields=[self.file_field_name, 'updated_at'])
            else:
                return self.error_response(
                    _('Unsupported model or file field'),
                    'configuration_error',
                    status.HTTP_400_BAD_REQUEST
                )

            # Return success response
            return self.success_response(
                data={
                    'count': len(new_files),
                    self.file_field_name: new_files
                },
                message=_('Files uploaded successfully'),
                status_code=status.HTTP_201_CREATED
            )

        except PermissionDenied as e:
            return self.permission_denied(str(e))
        except Http404:
            return self.not_found(f"{self.model_class.__name__} not found")
        except ValueError as e:
            return self.error_response(str(e), 'validation_error', status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error uploading files: {str(e)}")
            return self.error_response(
                _('Failed to process file uploads'),
                'upload_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# Media Upload Views - Unified approach using MediaHandler
# ============================================================================

class MediaUploadView(BaseAPIView):
    """
    Unified media upload view for handling file uploads across different entity types.
    This replaces multiple redundant upload views with a single, configurable implementation.
    """
    permission_classes = [permissions.IsAuthenticated]

    # Configuration to be set by subclasses
    entity_model = None
    entity_type = None
    media_type = 'image'
    max_files = 10

    def get_entity(self, pk):
        """Get the entity and verify permissions"""
        if not self.entity_model:
            raise ValueError("entity_model must be set in subclass")

        entity = get_object_or_404(self.entity_model, pk=pk)
        user = self.request.user

        # Check permissions based on entity type
        if not user.is_staff:
            if hasattr(entity, 'owner') and entity.owner != user:
                if hasattr(entity, 'created_by') and entity.created_by != user:
                    if hasattr(entity, 'auctioneer') and entity.auctioneer != user:
                        raise PermissionDenied(_("You don't have permission to upload files for this {entity_type}"))

        return entity

    @handle_exceptions
    @transaction.atomic
    def post(self, request, pk):
        """Upload files for an entity"""
        try:
            # Get entity and check permissions
            entity = self.get_entity(pk)

            # Determine field name based on media type
            field_name = 'files' if self.media_type == 'document' else 'images'

            # Check if files were provided
            if field_name not in request.FILES:
                return self.error_response(
                    _('No files were provided'),
                    'no_files',
                    status.HTTP_400_BAD_REQUEST
                )

            # Get files
            files = request.FILES.getlist(field_name)

            # Check for max files
            if len(files) > self.max_files:
                return self.error_response(
                    _('Too many files. Maximum is {max} files per upload.').format(max=self.max_files),
                    'too_many_files',
                    status.HTTP_400_BAD_REQUEST
                )

            # Process uploads based on entity and media type
            if self.entity_type == 'property' and self.media_type == 'image':
                new_files = MediaHandler.process_property_images(entity, files)
            elif self.entity_type == 'auction' and self.media_type == 'image':
                new_files = MediaHandler.process_auction_images(entity, files)
            elif self.entity_type == 'document' and self.media_type == 'document':
                new_files = MediaHandler.process_document_files(entity, files)
            else:
                return self.error_response(
                    _('Unsupported entity or media type'),
                    'configuration_error',
                    status.HTTP_400_BAD_REQUEST
                )

            # Return success response
            return self.success_response(
                data={
                    'count': len(new_files),
                    field_name: new_files
                },
                message=_('Files uploaded successfully'),
                status_code=status.HTTP_201_CREATED
            )

        except PermissionDenied as e:
            return self.permission_denied(str(e))
        except Http404:
            return self.not_found(f"{self.entity_type.title()} not found")
        except ValueError as e:
            return self.error_response(str(e), 'validation_error', status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error uploading files: {str(e)}")
            return self.error_response(
                _('Failed to process file uploads'),
                'upload_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PropertyImageUploadView(MediaUploadView):
    """Upload images for a property"""
    entity_model = Property
    entity_type = 'property'
    media_type = 'image'
    max_files = 10


class PropertyImageSetPrimaryView(BaseAPIView):
    """Set a primary image for a property"""
    permission_classes = [permissions.IsAuthenticated]

    @handle_exceptions
    def post(self, request, pk):
        """Set a property image as primary"""
        try:
            # Get property and check permissions
            property_obj = get_object_or_404(Property, pk=pk)

            if not request.user.is_staff and property_obj.owner != request.user:
                return self.permission_denied(_('You do not have permission to modify this property'))

            # Get image index
            try:
                image_index = int(request.data.get('image_index', -1))
            except (TypeError, ValueError):
                return self.error_response(_('Invalid image index'), 'invalid_index', status.HTTP_400_BAD_REQUEST)

            # Set primary image
            primary_image = MediaHandler.set_primary_image(property_obj, image_index)

            return self.success_response(
                data={'image': primary_image},
                message=_('Primary image set successfully')
            )

        except Http404:
            return self.not_found(_('Property not found'))
        except ValueError as e:
            return self.error_response(str(e), 'invalid_index', status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error setting primary image: {str(e)}")
            return self.error_response(_('Failed to set primary image'), 'update_error', status.HTTP_500_INTERNAL_SERVER_ERROR)


class PropertyImageDeleteView(BaseAPIView):
    """Delete a property image"""
    permission_classes = [permissions.IsAuthenticated]

    @handle_exceptions
    @transaction.atomic
    def delete(self, request, pk, image_index):
        """Delete an image from a property"""
        try:
            # Get property and check permissions
            property_obj = get_object_or_404(Property, pk=pk)

            if not request.user.is_staff and property_obj.owner != request.user:
                return self.permission_denied(_('You do not have permission to modify this property'))

            # Convert image_index to integer
            try:
                image_index = int(image_index)
            except ValueError:
                return self.error_response(_('Invalid image index'), 'invalid_index', status.HTTP_400_BAD_REQUEST)

            # Delete the image
            deleted_image = MediaHandler.delete_image(property_obj, image_index)

            return self.success_response(
                data={'deleted_image': deleted_image},
                message=_('Image deleted successfully')

)

        except Http404:
            return self.not_found(_('Property not found'))
        except ValueError as e:
            return self.error_response(str(e), 'invalid_index', status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error deleting image: {str(e)}")
            return self.error_response(_('Failed to delete image'), 'delete_error', status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuctionImageUploadView(MediaUploadView):
    """Upload images for an auction"""
    entity_model = Auction
    entity_type = 'auction'
    media_type = 'image'
    max_files = 10


class DocumentFileUploadView(MediaUploadView):
    """Upload files for a document"""
    entity_model = Document
    entity_type = 'document'
    media_type = 'document'
    max_files = 5



class PropertyListCreateView(BaseAPIView):
    """List and create properties"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [IsSellerPermission],
    }

    def get_queryset(self):
        """Get filtered property queryset"""
        queryset = Property.objects.all()
        params = self.request.query_params

        # Show only published properties to non-staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)

        # Apply filters
        filters = {k: v for k, v in params.items()
                  if k in ['status', 'property_type', 'city', 'district',
                          'bedrooms', 'bathrooms'] and v}

        if filters:
            queryset = queryset.filter(**filters)

        # Apply search
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(address__icontains=search) |
                Q(property_number__icontains=search)
            )

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['created_at', 'estimated_value', 'area', 'views_count']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get(self, request, format=None):
        """List properties"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PropertySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PropertySerializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    @transaction.atomic
    def post(self, request, format=None):
        """Create a property"""
        serializer = PropertySerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors, 'validation_error')

        try:
            property_obj = serializer.save(owner=request.user)
            return self.success_response(
                data=serializer.data,
                message=_('Property created successfully'),
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating property: {str(e)}")
            return self.error_response(_('Failed to create property'), 'creation_failed',
                                      status.HTTP_500_INTERNAL_SERVER_ERROR)

class PropertyDetailView(BaseAPIView):
    """Retrieve, update and delete a property"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [IsPropertyOwner],
        'patch': [IsPropertyOwner],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get property with permission check"""
        property_obj = get_object_or_404(Property, pk=pk)
        self.check_object_permissions(self.request, property_obj)
        return property_obj

    def get(self, request, pk, format=None):
        """Retrieve a property"""
        property_obj = self.get_object(pk)
        serializer = PropertySerializer(property_obj)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a property"""
        property_obj = self.get_object(pk)
        serializer = PropertySerializer(property_obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a property"""
        property_obj = self.get_object(pk)
        serializer = PropertySerializer(property_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a property"""
        property_obj = self.get_object(pk)
        property_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PropertyBySlugView(BaseAPIView):
    """Retrieve a property by slug"""
    permission_classes = [permissions.IsAuthenticated]

    @debug_request
    @cache_view(timeout=CACHE_MEDIUM, key_prefix='property_slug', vary_on_user=False)
    def get(self, request, slug, format=None):
        """Get property by slug and increment view count"""
        try:
            # Filter by user permissions
            queryset = Property.objects.all()
            if not request.user.is_staff:
                queryset = queryset.filter(is_published=True)

            property_obj = get_object_or_404(queryset, slug=slug)

            # Increment views count atomically
            with transaction.atomic():
                Property.objects.filter(pk=property_obj.pk).update(views_count=F('views_count') + 1)
                property_obj.refresh_from_db()

            serializer = PropertySerializer(property_obj)
            return self.success_response(data=serializer.data)
        except Http404:
            return self.not_found(f"Property with slug '{slug}' not found")
        except Exception as e:
            logger.error(f"Error retrieving property by slug '{slug}': {str(e)}")
            return self.error_response("An error occurred", "retrieval_error",
                                      status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyPropertiesView(BaseAPIView):
    """List properties owned by current user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's properties"""
        properties = Property.objects.filter(owner=request.user)

        # Handle pagination
        page = self.paginate_queryset(properties)
        if page is not None:
            serializer = PropertySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PropertySerializer(properties, many=True)
        return Response(serializer.data)

class VerifyPropertyView(BaseAPIView):
    """Verify a property"""
    permission_classes = [IsInspectorPermission]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Mark property as verified"""
        property_obj = get_object_or_404(Property, pk=pk)

        # Already verified
        if property_obj.is_verified:
            return Response({'status': 'Property already verified'})

        # Update verification status
        property_obj.is_verified = True
        property_obj.verified_by = request.user
        property_obj.verification_date = timezone.now()
        property_obj.save(update_fields=['is_verified', 'verified_by', 'verification_date', 'updated_at'])

        return Response({'status': 'Property verified'})



##### ======> Auction Views

class AuctionListCreateView(BaseAPIView):
    """List and create auctions"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [IsSellerPermission | IsAgentPermission],
    }

    def get_queryset(self):
        """Get filtered auction queryset"""
        queryset = Auction.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter for non-staff users
        if not user.is_staff:
            queryset = queryset.filter(
                # Public or user is invited to private
                (Q(is_private=False) | Q(is_private=True, invited_bidders=user)),
                is_published=True
            )

        # Apply filters
        filters = {}
        for field in ['status', 'auction_type']:
            if params.get(field):
                filters[field] = params.get(field)

        # Boolean filters
        for field in ['is_featured', 'is_published']:
            if params.get(field) is not None:
                filters[field] = params.get(field).lower() == 'true'

        if filters:
            queryset = queryset.filter(**filters)

        # Apply search
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['start_date', 'end_date', 'current_bid', 'views_count']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get(self, request, format=None):
        """List auctions"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AuctionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AuctionSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """Create an auction"""
        serializer = AuctionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                created_by=request.user,
                # If no auctioneer specified, use current user
                auctioneer=serializer.validated_data.get('auctioneer', request.user)
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class AuctionDetailView(BaseAPIView):
    """Retrieve, update and delete an auction"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [IsAuctionCreator],
        'patch': [IsAuctionCreator],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get auction with permission check"""
        auction = get_object_or_404(Auction, pk=pk)
        self.check_object_permissions(self.request, auction)
        return auction

    def get(self, request, pk, format=None):
        """Retrieve an auction"""
        auction = self.get_object(pk)
        serializer = AuctionSerializer(auction)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update an auction"""
        auction = self.get_object(pk)
        serializer = AuctionSerializer(auction, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update an auction"""
        auction = self.get_object(pk)
        serializer = AuctionSerializer(auction, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete an auction"""
        auction = self.get_object(pk)
        auction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AuctionBySlugView(BaseAPIView):
    """Retrieve an auction by slug"""
    permission_classes = [permissions.IsAuthenticated]

    @debug_request
    @cache_view(timeout=CACHE_SHORT, key_prefix='auction_slug', vary_on_user=True)
    def get(self, request, slug, format=None):
        """Get auction by slug and increment view count"""
        user = request.user

        # Get accessible auctions
        if user.is_staff:
            queryset = Auction.objects.all()
        else:
            queryset = Auction.objects.filter(
                # Public or user is invited
                (Q(is_private=False) | Q(is_private=True, invited_bidders=user))
            )

        auction = get_object_or_404(queryset, slug=slug)

        # Increment views count atomically
        with transaction.atomic():
            Auction.objects.filter(pk=auction.pk).update(views_count=F('views_count') + 1)
            auction.refresh_from_db()

        serializer = AuctionSerializer(auction)
        return Response(serializer.data)

class MyAuctionsView(BaseAPIView):
    """List auctions the user is involved with"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's auctions"""
        auctions = Auction.objects.filter(
            Q(created_by=request.user) |
            Q(auctioneer=request.user) |
            Q(invited_bidders=request.user)
        ).distinct()

        # Handle pagination
        page = self.paginate_queryset(auctions)
        if page is not None:
            serializer = AuctionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AuctionSerializer(auctions, many=True)
        return Response(serializer.data)

class ExtendAuctionView(BaseAPIView):
    """Extend an auction's end time"""
    permission_classes = [IsAuctionCreator]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Extend auction duration"""
        try:
            auction = get_object_or_404(Auction, pk=pk)
            minutes = request.data.get('minutes', auction.extension_minutes)

            # Validate auction status
            if auction.status not in ['active', 'extended']:
                return self.error_response(
                    'Only active or extended auctions can be extended',
                    'invalid_status',
                    status.HTTP_400_BAD_REQUEST
                )

            # Extend the auction
            success = auction.extend_auction(minutes=minutes)

            if success:
                return self.success_response(
                    message=f'Auction extended by {minutes} minutes'
                )

            return self.error_response('Failed to extend auction', 'extension_failed')
        except Http404:
            return self.not_found('Auction not found')
        except Exception as e:
            logger.error(f"Error extending auction: {str(e)}")
            return self.error_response('An error occurred', 'extension_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)

class CloseAuctionView(BaseAPIView):
    """Close an auction before its end time"""
    permission_classes = [IsAuctionCreator]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Close an auction manually"""
        try:
            auction = get_object_or_404(Auction, pk=pk)

            # Validate auction status
            if auction.status not in ['active', 'extended']:
                return self.error_response(
                    f'Only active or extended auctions can be closed',
                    'invalid_status',
                    status.HTTP_400_BAD_REQUEST
                )

            # Check if already ended naturally
            now = timezone.now()
            if now > auction.end_date:
                return self.error_response(
                    'Auction has already ended naturally',
                    'already_ended',
                    status.HTTP_400_BAD_REQUEST
                )

            # Close the auction
            auction.status = 'closed'
            auction.end_reason = request.data.get('reason', 'Manually closed by auctioneer')
            auction.end_date = timezone.now()
            auction.save(update_fields=['status', 'end_reason', 'end_date', 'updated_at'])

            return self.success_response(message='Auction closed successfully')
        except Http404:
            return self.not_found('Auction not found')
        except Exception as e:
            logger.error(f"Error closing auction: {str(e)}")
            return self.error_response('An error occurred', 'closure_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)

# Fix for UploadAuctionImagesView - replace BaseUploadView with our new class
class UploadAuctionImagesView(BaseUploadView):
    """Upload images for an auction"""
    model_class = Auction
    file_field_name = 'images'
    allow_multiple = True
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    max_file_size = 5 * 1024 * 1024  # 5MB







# Bid Views
class PlaceBidView(BaseAPIView):
    """Place a bid on an auction"""
    permission_classes = [permissions.IsAuthenticated]

    def validate_bid(self, auction, user, bid_amount):
        """Validate bid parameters"""
        # Check if auction is active
        if auction.status != 'active':
            return False, 'Cannot bid on inactive auction', 'inactive_auction', status.HTTP_400_BAD_REQUEST

        # Check if auction is open
        now = timezone.now()
        if now < auction.start_date or now > auction.end_date:
            return False, 'Auction is not open for bids', 'auction_closed', status.HTTP_400_BAD_REQUEST

        # Check if private and user is invited
        if auction.is_private and user not in auction.invited_bidders.all():
            return False, 'You are not invited to this auction', 'not_invited', status.HTTP_403_FORBIDDEN

        # Validate bid amount
        if bid_amount is None:
            return False, 'Bid amount is required', 'missing_amount', status.HTTP_400_BAD_REQUEST

        try:
            bid_amount = float(bid_amount)
        except (ValueError, TypeError):
            return False, 'Invalid bid amount format', 'invalid_format', status.HTTP_400_BAD_REQUEST

        # Check if bid is high enough
        highest_bid = auction.highest_bid
        min_bid = highest_bid + auction.min_bid_increment

        if bid_amount < min_bid:
            return False, f'Bid amount must be at least {min_bid}', 'bid_too_low', status.HTTP_400_BAD_REQUEST

        return True, None, None, None

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Place a bid"""
        try:
            auction = get_object_or_404(Auction, pk=pk)
        except Http404:
            return self.not_found('Auction not found')

        # Validate bid
        bid_amount = request.data.get('bid_amount')
        is_valid, error_msg, error_code, error_status = self.validate_bid(
            auction, request.user, bid_amount
        )

        if not is_valid:
            return self.error_response(error_msg, error_code, error_status)

        # Create bid
        bid_data = {
            'auction': auction.id,
            'bidder': request.user.id,
            'bid_amount': float(bid_amount),
            'max_bid_amount': request.data.get('max_bid_amount'),
            'is_auto_bid': bool(request.data.get('max_bid_amount')),
        }

        serializer = BidSerializer(data=bid_data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors, 'validation_error')

        # Save bid with meta data
        bid = serializer.save(
            bidder=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

        # Auto-extend if bid is near the end
        now = timezone.now()
        time_left = (auction.end_date - now).total_seconds() / 60
        if auction.auto_extend and time_left <= auction.extension_minutes:
            auction.extend_auction()

        return self.success_response(
            data=serializer.data,
            message='Bid placed successfully',
            status_code=status.HTTP_201_CREATED
        )

class BidListCreateView(BaseAPIView):
    """List and create bids"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def get_queryset(self):
        """Get filtered bid queryset"""
        queryset = Bid.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter for non-staff users
        if not user.is_staff:
            queryset = queryset.filter(
                Q(bidder=user) |
                Q(auction__created_by=user) |
                Q(auction__auctioneer=user)
            )

        # Apply filters
        if params.get('auction'):
            queryset = queryset.filter(auction=params.get('auction'))

        if params.get('bidder'):
            queryset = queryset.filter(bidder=params.get('bidder'))

        if params.get('status'):
            queryset = queryset.filter(status=params.get('status'))

        if params.get('is_auto_bid') is not None:
            is_auto = params.get('is_auto_bid').lower() == 'true'
            queryset = queryset.filter(is_auto_bid=is_auto)

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['bid_amount', 'bid_time']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-bid_time')

        return queryset

    def get(self, request, format=None):
        """List bids"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BidSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BidSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """Create a bid"""
        serializer = BidSerializer(data=request.data)
        if serializer.is_valid():
            # Check if user can bid on this auction
            auction = serializer.validated_data.get('auction')
            user = request.user

            if auction.is_private and user not in auction.invited_bidders.all():
                return Response(
                    {"error": "You are not invited to this private auction"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Save bid with meta data
            bid = serializer.save(
                bidder=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BidDetailView(BaseAPIView):
    """Retrieve, update and delete a bid"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAdminUser],
        'patch': [permissions.IsAdminUser],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get bid with permission check"""
        user = self.request.user

        # Filter based on permissions
        if user.is_staff:
            queryset = Bid.objects.all()
        else:
            queryset = Bid.objects.filter(
                Q(bidder=user) |
                Q(auction__created_by=user) |
                Q(auction__auctioneer=user)
            )

        bid = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, bid)
        return bid

    def get(self, request, pk, format=None):
        """Retrieve a bid"""
        bid = self.get_object(pk)
        serializer = BidSerializer(bid)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a bid"""
        bid = self.get_object(pk)
        serializer = BidSerializer(bid, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a bid"""
        bid = self.get_object(pk)
        serializer = BidSerializer(bid, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a bid"""
        bid = self.get_object(pk)
        bid.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MyBidsView(BaseAPIView):
    """List bids placed by current user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's bids"""
        bids = Bid.objects.filter(bidder=request.user)

        # Filter by auction if specified
        auction_id = request.query_params.get('auction_id')
        if auction_id:
            bids = bids.filter(auction_id=auction_id)

        # Handle pagination
        page = self.paginate_queryset(bids)
        if page is not None:
            serializer = BidSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BidSerializer(bids, many=True)
        return Response(serializer.data)

class MarkBidAsWinningView(BaseAPIView):
    """Mark a bid as the winning bid"""
    permission_classes = [IsAgentPermission]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Mark bid as winning"""
        try:
            bid = get_object_or_404(Bid, pk=pk)
            auction = bid.auction

            # Check permissions
            user = request.user
            if not user.is_staff and user != auction.created_by and user != auction.auctioneer:
                return self.permission_denied('You do not have permission to mark the winning bid')

            # Check auction status
            if auction.status not in ['closed', 'extended', 'active']:
                return self.error_response(
                    f'Cannot mark winning bid for auction with status {auction.status}',
                    'invalid_status',
                    status.HTTP_400_BAD_REQUEST
                )

            # Check if already has a winner
            if auction.winning_bidder is not None:
                return self.error_response(
                    'This auction already has a winning bid',
                    'winner_exists',
                    status.HTTP_400_BAD_REQUEST
                )

            # Mark as winning
            success = bid.mark_as_winning()

            if success:
                return self.success_response(message='Bid marked as winning successfully')

            return self.error_response('Failed to mark bid as winning', 'marking_failed')
        except Http404:
            return self.not_found('Bid not found')
        except Exception as e:
            logger.error(f"Error marking bid as winning: {str(e)}")
            return self.error_response('An error occurred', 'marking_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)


# Document Views
class DocumentListCreateView(BaseAPIView):
    """List and create documents"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def get_queryset(self):
        """Get filtered document queryset"""
        queryset = Document.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter for non-staff users
        if not user.is_staff:
            queryset = queryset.filter(
                Q(uploaded_by=user) |
                Q(related_property__owner=user) |
                Q(auction__created_by=user) |
                Q(auction__auctioneer=user) |
                Q(contract__buyer=user) |
                Q(contract__seller=user) |
                Q(contract__agent=user)
            )

        # Apply filters
        filters = {}
        for field in ['document_type', 'verification_status', 'related_property', 'auction', 'contract']:
            if params.get(field):
                filters[field] = params.get(field)

        if filters:
            queryset = queryset.filter(**filters)

        # Apply search
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(document_number__icontains=search)
            )

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['created_at', 'issue_date', 'expiry_date']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get(self, request, format=None):
        """List documents"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = DocumentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DocumentSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """Create a document"""
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save(uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentDetailView(BaseAPIView):
    """Retrieve, update and delete a document"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAuthenticated],
        'patch': [permissions.IsAuthenticated],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get document with permission check"""
        document = get_object_or_404(Document, pk=pk)
        self.check_object_permissions(self.request, document)

        # Additional permission check for updates
        if self.request.method in ['PUT', 'PATCH']:
            user = self.request.user
            if (user != document.uploaded_by and
                not user.is_staff and
                not user.has_role(Role.LEGAL)):
                raise PermissionDenied("You don't have permission to update this document")

        return document

    def get(self, request, pk, format=None):
        """Retrieve a document"""
        document = self.get_object(pk)
        serializer = DocumentSerializer(document)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a document"""
        document = self.get_object(pk)
        serializer = DocumentSerializer(document, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a document"""
        document = self.get_object(pk)
        serializer = DocumentSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a document"""
        document = self.get_object(pk)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class VerifyDocumentView(BaseAPIView):
    """Verify a document"""
    permission_classes = [IsLegalPermission | IsInspectorPermission]

    def post(self, request, pk, format=None):
        """Mark document as verified"""
        document = get_object_or_404(Document, pk=pk)
        notes = request.data.get('notes')

        # Execute verification
        success = document.verify(user=request.user, notes=notes)

        if success:
            return Response({'status': 'Document verified'})
        return Response(
            {'error': 'Failed to verify document'},
            status=status.HTTP_400_BAD_REQUEST
        )

class MyDocumentsView(BaseAPIView):
    """List documents uploaded by current user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's documents"""
        documents = Document.objects.filter(uploaded_by=request.user)

        # Filter by type if specified
        doc_type = request.query_params.get('document_type')
        if doc_type:
            documents = documents.filter(document_type=doc_type)

        # Handle pagination
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = DocumentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)

# Replace BaseUploadView with our implementation
class UploadDocumentFilesView(BaseUploadView):
    """Upload files to a document"""
    model_class = Document
    file_field_name = 'files'
    allow_multiple = True
    allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
    max_file_size = 10 * 1024 * 1024  # 10MB


# Contract Views
class ContractListCreateView(BaseAPIView):
    """List and create contracts"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [IsLegalPermission | IsAgentPermission],
    }

    def get_queryset(self):
        """Get filtered contract queryset"""
        queryset = Contract.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter for non-staff users
        if not user.is_staff:
            queryset = queryset.filter(
                Q(buyer=user) |
                Q(seller=user) |
                Q(agent=user) |
                Q(auction__created_by=user) |
                Q(auction__auctioneer=user)
            )

        # Apply filters
        filters = {}
        for field in ['status', 'buyer', 'seller', 'agent', 'related_property', 'auction']:
            if params.get(field):
                filters[field] = params.get(field)

        if filters:
            queryset = queryset.filter(**filters)

        # Apply search
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(contract_number__icontains=search)
            )

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['created_at', 'contract_date', 'contract_amount']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get(self, request, format=None):
        """List contracts"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ContractSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ContractSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """Create a contract"""
        serializer = ContractSerializer(data=request.data)
        if serializer.is_valid():
            contract = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ContractDetailView(BaseAPIView):
    """Retrieve, update and delete a contract"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [IsLegalPermission | IsAgentPermission],
        'patch': [IsLegalPermission | IsAgentPermission],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get contract with permission check"""
        contract = get_object_or_404(Contract, pk=pk)
        self.check_object_permissions(self.request, contract)
        return contract

    def get(self, request, pk, format=None):
        """Retrieve a contract"""
        contract = self.get_object(pk)
        serializer = ContractSerializer(contract)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a contract"""
        contract = self.get_object(pk)
        serializer = ContractSerializer(contract, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a contract"""
        contract = self.get_object(pk)
        serializer = ContractSerializer(contract, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a contract"""
        contract = self.get_object(pk)
        contract.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Replace BaseUploadView with our implementation
class UploadContractFilesView(BaseUploadView):
    """Upload files to a contract"""
    model_class = Contract
    file_field_name = 'files'
    allow_multiple = True
    allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
    max_file_size = 10 * 1024 * 1024  # 10MB

class SignContractAsBuyerView(BaseAPIView):
    """Sign a contract as buyer"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Sign contract as buyer"""
        try:
            contract = get_object_or_404(Contract, pk=pk)
            user = request.user

            # Verify user is the buyer
            if user != contract.buyer:
                return self.permission_denied('You are not the buyer for this contract')

            # Check if already signed
            if contract.buyer_signed:
                return self.success_response(message='Contract already signed by buyer')

            # Sign the contract
            success = contract.sign_as_buyer(user=user)

            if success:
                return self.success_response(message='Contract signed successfully')

            return self.error_response('Failed to sign contract', 'signing_failed')
        except Http404:
            return self.not_found('Contract not found')
        except Exception as e:
            logger.error(f"Error signing contract as buyer: {str(e)}")
            return self.error_response('An error occurred', 'signing_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)

class SignContractAsSellerView(BaseAPIView):
    """Sign a contract as seller"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Sign contract as seller"""
        try:
            contract = get_object_or_404(Contract, pk=pk)
            user = request.user

            # Verify user is the seller
            if user != contract.seller:
                return self.permission_denied('You are not the seller for this contract')

            # Check if already signed
            if contract.seller_signed:
                return self.success_response(message='Contract already signed by seller')

            # Sign the contract
            success = contract.sign_as_seller(user=user)

            if success:
                return self.success_response(message='Contract signed successfully')

            return self.error_response('Failed to sign contract', 'signing_failed')
        except Http404:
            return self.not_found('Contract not found')
        except Exception as e:
            logger.error(f"Error signing contract as seller: {str(e)}")
            return self.error_response('An error occurred', 'signing_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)

class SignContractAsAgentView(BaseAPIView):
    """Sign a contract as agent"""
    permission_classes = [IsAgentPermission]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Sign contract as agent"""
        try:
            contract = get_object_or_404(Contract, pk=pk)
            user = request.user

            # Verify user is the agent
            if user != contract.agent:
                return self.permission_denied('You are not the agent for this contract')

            # Check if already signed
            if contract.agent_signed:
                return self.success_response(message='Contract already signed by agent')

            # Sign as agent
            contract.agent_signed = True
            contract.agent_signature_date = timezone.now()

            # Update status if all parties signed
            if contract.buyer_signed and contract.seller_signed:
                contract.status = 'signed'

            contract.save(update_fields=[
                'agent_signed', 'agent_signature_date', 'status', 'updated_at'
            ])

            return self.success_response(message='Contract signed successfully')
        except Http404:
            return self.not_found('Contract not found')
        except Exception as e:
            logger.error(f"Error signing contract as agent: {str(e)}")
            return self.error_response('An error occurred', 'signing_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)

class MyContractsView(BaseAPIView):
    """List contracts the user is involved with"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's contracts"""
        user = request.user
        contracts = Contract.objects.filter(
            Q(buyer=user) |
            Q(seller=user) |
            Q(agent=user)
        )

        # Filter by status if specified
        status_filter = request.query_params.get('status')
        if status_filter:
            contracts = contracts.filter(status=status_filter)

        # Handle pagination
        page = self.paginate_queryset(contracts)
        if page is not None:
            serializer = ContractSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ContractSerializer(contracts, many=True)
        return Response(serializer.data)


# Payment Views
class PaymentListCreateView(BaseAPIView):
    """List and create payments"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def get_queryset(self):
        """Get filtered payment queryset"""
        queryset = Payment.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter for non-staff users
        if not user.is_staff and not user.has_role(Role.AGENT):
            queryset = queryset.filter(
                Q(payer=user) |
                Q(payee=user) |
                Q(contract__buyer=user) |
                Q(contract__seller=user) |
                Q(contract__agent=user)
            )

        # Apply filters
        filters = {}
        for field in ['status', 'payment_type', 'payment_method', 'contract', 'payer', 'payee']:
            if params.get(field):
                filters[field] = params.get(field)

        if filters:
            queryset = queryset.filter(**filters)

        # Apply search
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(payment_number__icontains=search) |
                Q(transaction_reference__icontains=search)
            )

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['payment_date', 'amount', 'created_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-payment_date')

        return queryset

    def get(self, request, format=None):
        """List payments"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PaymentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PaymentSerializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    @transaction.atomic
    def post(self, request, format=None):
        """Create a payment"""
        serializer = PaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors, 'validation_error')

        try:
            payment = serializer.save(payer=request.user)
            return self.success_response(
                data=serializer.data,
                message='Payment created successfully',
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            return self.error_response('Failed to create payment', 'creation_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentDetailView(BaseAPIView):
    """Retrieve, update and delete a payment"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAdminUser | IsAgentPermission],
        'patch': [permissions.IsAdminUser | IsAgentPermission],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get payment with permission check"""
        payment = get_object_or_404(Payment, pk=pk)
        self.check_object_permissions(self.request, payment)
        return payment

    def get(self, request, pk, format=None):
        """Retrieve a payment"""
        payment = self.get_object(pk)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a payment"""
        payment = self.get_object(pk)
        serializer = PaymentSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a payment"""
        payment = self.get_object(pk)
        serializer = PaymentSerializer(payment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a payment"""
        payment = self.get_object(pk)
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ConfirmPaymentView(BaseAPIView):
    """Confirm a payment"""
    permission_classes = [IsAgentPermission]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Confirm a payment"""
        try:
            payment = get_object_or_404(Payment, pk=pk)

            # Check if already confirmed
            if payment.status == 'completed':
                return self.success_response(message='Payment already confirmed')

            # Verify payment status allows confirmation
            if payment.status not in ['pending', 'processing']:
                return self.error_response(
                    f'Cannot confirm payment with status {payment.status}',
                    'invalid_status',
                    status.HTTP_400_BAD_REQUEST
                )

            # Confirm the payment
            success = payment.confirm_payment(user=request.user)

            if success:
                return self.success_response(message='Payment confirmed successfully')

            return self.error_response('Failed to confirm payment', 'confirmation_failed')
        except Http404:
            return self.not_found('Payment not found')
        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}")
            return self.error_response('An error occurred', 'confirmation_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)

class MyPaymentsView(BaseAPIView):
    """List payments made or received by current user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's payments"""
        user = request.user
        payments = Payment.objects.filter(
            Q(payer=user) |
            Q(payee=user)
        )

        # Filter by type
        payment_type = request.query_params.get('payment_type')
        if payment_type:
            payments = payments.filter(payment_type=payment_type)

        # Filter by direction
        direction = request.query_params.get('direction')
        if direction == 'made':
            payments = payments.filter(payer=user)
        elif direction == 'received':
            payments = payments.filter(payee=user)

        # Handle pagination
        page = self.paginate_queryset(payments)
        if page is not None:
            serializer = PaymentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

# Replace BaseUploadView with our implementation
class UploadPaymentReceiptView(BaseUploadView):
    """Upload receipt for a payment"""
    model_class = Payment
    file_field_name = 'receipt'
    allow_multiple = False
    allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
    max_file_size = 5 * 1024 * 1024  # 5MB

    def get_object(self, pk):
        """Get payment with permission check"""
        payment = get_object_or_404(Payment, pk=pk)

        # Check permission
        user = self.request.user
        if user != payment.payer and not user.is_staff and not user.has_role(Role.AGENT):
            raise PermissionDenied("You don't have permission to upload receipt for this payment")

        return payment


# Message Thread Views
class MessageThreadListCreateView(BaseAPIView):
    """List and create message threads"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def get_queryset(self):
        """Get filtered message thread queryset"""
        queryset = MessageThread.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter for non-staff users
        if not user.is_staff:
            queryset = queryset.filter(
                thread_participants__user=user,
                thread_participants__is_active=True
            )

        # Apply filters
        filters = {}
        for field in ['thread_type', 'status']:
            if params.get(field):
                filters[field] = params.get(field)

        # Boolean filters
        for field in ['is_private', 'is_system_thread']:
            if params.get(field) is not None:
                filters[field] = params.get(field).lower() == 'true'

        if params.get('creator'):
            filters['creator'] = params.get('creator')

        if filters:
            queryset = queryset.filter(**filters)

        # Apply search
        search = params.get('search')
        if search:
            queryset = queryset.filter(subject__icontains=search)

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['last_message_at', 'created_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-last_message_at', '-created_at')

        return queryset

    def get(self, request, format=None):
        """List message threads"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MessageThreadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageThreadSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """Create a message thread"""
        serializer = MessageThreadSerializer(data=request.data)
        if serializer.is_valid():
            thread = serializer.save(creator=request.user)

            # Add creator as participant
            ThreadParticipant.objects.create(
                thread=thread,
                user=request.user,
                is_active=True
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageThreadDetailView(BaseAPIView):
    """Retrieve, update and delete a message thread"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAuthenticated],
        'patch': [permissions.IsAuthenticated],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get message thread with permission check"""
        thread = get_object_or_404(MessageThread, pk=pk)
        self.check_object_permissions(self.request, thread)

        # Additional permission check for updates
        if self.request.method in ['PUT', 'PATCH']:
            user = self.request.user
            if (user != thread.creator and
                not user.is_staff and
                not ThreadParticipant.objects.filter(
                    thread=thread,
                    user=user,
                    is_active=True,
                    role__name__in=['admin', 'moderator']
                ).exists()):
                raise PermissionDenied("You don't have permission to update this thread")

        return thread

    def get(self, request, pk, format=None):
        """Retrieve a message thread"""
        thread = self.get_object(pk)
        serializer = MessageThreadSerializer(thread)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a message thread"""
        thread = self.get_object(pk)
        serializer = MessageThreadSerializer(thread, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a message thread"""
        thread = self.get_object(pk)
        serializer = MessageThreadSerializer(thread, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a message thread"""
        thread = self.get_object(pk)
        thread.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ThreadBySlugView(BaseAPIView):
    """Retrieve a message thread by slug"""
    permission_classes = [permissions.IsAuthenticated]

    @debug_request
    @cache_view(timeout=CACHE_SHORT, key_prefix='thread_slug', vary_on_user=True)
    def get(self, request, slug, format=None):
        """Get thread by slug"""
        user = request.user

        if user.is_staff:
            queryset = MessageThread.objects.all()
        else:
            queryset = MessageThread.objects.filter(
                thread_participants__user=user,
                thread_participants__is_active=True
            )

        thread = get_object_or_404(queryset, slug=slug)
        serializer = MessageThreadSerializer(thread)
        return Response(serializer.data)

class AddThreadParticipantView(BaseAPIView):
    """Add a participant to a thread"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Add participant to thread"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check permission to add participants
        if (user != thread.creator and
            not user.is_staff and
            not ThreadParticipant.objects.filter(
                thread=thread,
                user=user,
                is_active=True,
                role__name__in=['admin', 'moderator']
            ).exists()):
            return Response(
                {'error': "You don't have permission to add participants"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get user to add
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'User ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_to_add = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Add participant
        role = request.data.get('role', 'member')
        participant = thread.add_participant(user_to_add, role=role)

        return Response({'status': 'Participant added successfully'})

class RemoveThreadParticipantView(BaseAPIView):
    """Remove a participant from a thread"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Remove participant from thread"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check permission to remove participants
        if (user != thread.creator and
            not user.is_staff and
            not ThreadParticipant.objects.filter(
                thread=thread,
                user=user,
                is_active=True,
                role__name__in=['admin', 'moderator']
            ).exists()):
            return Response(
                {'error': "You don't have permission to remove participants"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get user to remove
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'User ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_to_remove = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Remove participant
        success = thread.remove_participant(user_to_remove)

        if success:
            return Response({'status': 'Participant removed successfully'})
        return Response(
            {'error': 'Failed to remove participant'},
            status=status.HTTP_400_BAD_REQUEST
        )

class MarkThreadAsReadView(BaseAPIView):
    """Mark all messages in a thread as read"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Mark thread as read"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check if user is participant
        participant = ThreadParticipant.objects.filter(
            thread=thread,
            user=user,
            is_active=True
        ).first()

        if not participant:
            return Response(
                {'error': 'You are not an active participant in this thread'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Mark thread as read
        count = participant.mark_all_as_read()

        return Response({'status': f'{count} messages marked as read'})

class CloseThreadView(BaseAPIView):
    """Close a thread"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Close a thread"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check if already closed
        if thread.status == 'closed':
            return Response({'status': 'Thread is already closed'})

        # Check permission to close
        if (user != thread.creator and
            not user.is_staff and
            not ThreadParticipant.objects.filter(
                thread=thread,
                user=user,
                is_active=True,
                role__name__in=['admin', 'moderator']
            ).exists()):
            return Response(
                {'error': "You don't have permission to close this thread"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Close thread
        thread.status = 'closed'
        thread.save(update_fields=['status', 'updated_at'])

        return Response({'status': 'Thread closed successfully'})

class ReopenThreadView(BaseAPIView):
    """Reopen a closed thread"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Reopen a thread"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check if already active
        if thread.status == 'active':
            return Response({'status': 'Thread is already active'})

        # Check permission to reopen
        if (user != thread.creator and
            not user.is_staff and
            not ThreadParticipant.objects.filter(
                thread=thread,
                user=user,
                is_active=True,
                role__name__in=['admin', 'moderator']
            ).exists()):
            return Response(
                {'error': "You don't have permission to reopen this thread"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Reopen thread
        thread.status = 'active'
        thread.save(update_fields=['status', 'updated_at'])

        return Response({'status': 'Thread reopened successfully'})

class MyThreadsView(BaseAPIView):
    """List threads the user is participating in"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's threads"""
        try:
            user = request.user
            threads = MessageThread.objects.filter(
                thread_participants__user=user,
                thread_participants__is_active=True
            ).distinct()

            # Filter by status
            status_filter = request.query_params.get('status')
            if status_filter:
                threads = threads.filter(status=status_filter)

            # Filter by unread
            unread_only = request.query_params.get('unread', 'false').lower() == 'true'
            if unread_only:
                # Get participant records for current user
                participant_subquery = ThreadParticipant.objects.filter(
                    thread=OuterRef('pk'),
                    user=user,
                    is_active=True
                )

                # Annotate with user's last_read_at
                threads = threads.annotate(
                    user_last_read=Subquery(
                        participant_subquery.values('last_read_at')[:1]
                    )
                )

                threads = threads.annotate(
                    has_unread=Exists(
                        Message.objects.filter(
                            thread=OuterRef('pk'),
                            sent_at__gt=OuterRef('user_last_read')
                        ).filter(~Q(sender=user))
                    )
                ).filter(has_unread=True)

            # Handle pagination
            page = self.paginate_queryset(threads)
            if page is not None:
                serializer = MessageThreadSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = MessageThreadSerializer(threads, many=True)
            return self.success_response(data=serializer.data)

        except Exception as e:
            logger.error(f"Error retrieving threads: {str(e)}")
            return self.error_response(
                error="An error occurred while retrieving threads",
                error_code="retrieval_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Message Views
class MessageListCreateView(BaseAPIView):
    """List and create messages"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def get_queryset(self):
        """Get filtered message queryset"""
        queryset = Message.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter for non-staff users
        if not user.is_staff:
            # Get threads user is participating in
            threads = MessageThread.objects.filter(
                thread_participants__user=user,
                thread_participants__is_active=True
            )
            queryset = queryset.filter(thread__in=threads)

        # Apply filters
        filters = {}

        if params.get('thread_id'):
            filters['thread_id'] = params.get('thread_id')

        if params.get('thread'):
            filters['thread'] = params.get('thread')

        if params.get('sender'):
            filters['sender'] = params.get('sender')

        if params.get('message_type'):
            filters['message_type'] = params.get('message_type')

        if params.get('status'):
            filters['status'] = params.get('status')

        # Boolean filters
        for field in ['is_system_message', 'is_important']:
            if params.get(field) is not None:
                filters[field] = params.get(field).lower() == 'true'

        if filters:
            queryset = queryset.filter(**filters)

        # Apply search
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(subject__icontains=search) |
                Q(content__icontains=search)
            )

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['sent_at', 'delivered_at', 'read_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-sent_at')

        return queryset

    def get(self, request, format=None):
        """List messages"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request, format=None):
        """Create a message"""
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            thread = serializer.validated_data.get('thread')
            user = request.user

            # Check if thread is closed
            if thread.status != 'active':
                return Response(
                    {"error": f"Cannot post to a {thread.get_status_display()} thread"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if user is active participant
            is_participant = ThreadParticipant.objects.filter(
                thread=thread,
                user=user,
                is_active=True
            ).exists()

            if not is_participant and not user.is_staff:
                return Response(
                    {"error": "You're not a participant in this thread"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Create message
            message = serializer.save(sender=user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageDetailView(BaseAPIView):
    """Retrieve, update and delete a message"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAuthenticated],
        'patch': [permissions.IsAuthenticated],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get message with permission check"""
        message = get_object_or_404(Message, pk=pk)
        self.check_object_permissions(self.request, message)

        # Additional permission check for updates
        if self.request.method in ['PUT', 'PATCH']:
            user = self.request.user
            if (user != message.sender and
                user != message.thread.creator and
                not user.is_staff):
                raise PermissionDenied("You don't have permission to update this message")

        return message

    def get(self, request, pk, format=None):
        """Retrieve a message"""
        message = self.get_object(pk)
        serializer = MessageSerializer(message)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a message"""
        message = self.get_object(pk)
        serializer = MessageSerializer(message, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a message"""
        message = self.get_object(pk)
        serializer = MessageSerializer(message, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a message"""
        message = self.get_object(pk)
        message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MarkMessageAsReadView(BaseAPIView):
    """Mark a message as read"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Mark message as read"""
        message = get_object_or_404(Message, pk=pk)
        user = request.user

        # Verify user is a participant
        is_participant = ThreadParticipant.objects.filter(
            thread=message.thread,
            user=user,
            is_active=True
        ).exists()

        if not is_participant and not user.is_staff:
            return Response(
                {'error': "You are not a participant in this thread"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Don't mark own messages
        if message.sender == user:
            return Response({'status': 'No need to mark your own messages as read'})

        # Mark as read
        success = message.mark_as_read(reader=user)

        if success:
            return Response({'status': 'Message marked as read'})
        return Response(
            {'error': 'Failed to mark message as read'},
            status=status.HTTP_400_BAD_REQUEST
        )

class MyMessagesView(BaseAPIView):
    """List messages sent by current user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's messages"""
        user = request.user
        messages = Message.objects.filter(sender=user)

        # Filter by thread if specified
        thread_id = request.query_params.get('thread_id')
        if thread_id:
            messages = messages.filter(thread_id=thread_id)

        # Handle pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)




class UploadMessageAttachmentView(BaseUploadView):
    """Upload attachment to a message"""
    model_class = Message
    file_field_name = 'attachments'
    allow_multiple = True
    allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'txt']
    max_file_size = 10 * 1024 * 1024  # 10MB

    def get_object(self, pk):
        """Get message with permission check"""
        message = get_object_or_404(Message, pk=pk)

        # Only sender can upload attachments
        user = self.request.user
        if user != message.sender and not user.is_staff:
            raise PermissionDenied("You can only upload attachments to your own messages")

        # Check if thread is active
        if message.thread.status != 'active':
            raise PermissionDenied("Cannot upload attachments to messages in closed threads")

        return message

# Transaction Views
class TransactionListCreateView(BaseAPIView):
    """List and create transactions"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [IsAgentPermission | permissions.IsAdminUser],
    }

    def get_queryset(self):
        """Get filtered transaction queryset"""
        queryset = Transaction.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter for non-staff/non-agent users
        if not user.is_staff and not user.has_role(Role.AGENT):
            queryset = queryset.filter(
                Q(from_user=user) |
                Q(to_user=user)
            )

        # Apply filters
        filters = {}
        for field in ['transaction_type', 'status', 'from_user', 'to_user',
                     'payment', 'auction', 'contract']:
            if params.get(field):
                filters[field] = params.get(field)

        if filters:
            queryset = queryset.filter(**filters)

        # Apply search
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(transaction_number__icontains=search) |
                Q(description__icontains=search) |
                Q(reference__icontains=search)
            )

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['transaction_date', 'amount', 'created_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-transaction_date')

        return queryset

    def get(self, request, format=None):
        """List transactions"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """Create a transaction"""
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionDetailView(BaseAPIView):
    """Retrieve, update and delete a transaction"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAdminUser],
        'patch': [permissions.IsAdminUser],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get transaction with permission check"""
        transaction = get_object_or_404(Transaction, pk=pk)
        self.check_object_permissions(self.request, transaction)
        return transaction

    def get(self, request, pk, format=None):
        """Retrieve a transaction"""
        transaction = self.get_object(pk)
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a transaction"""
        transaction = self.get_object(pk)
        serializer = TransactionSerializer(transaction, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a transaction"""
        transaction = self.get_object(pk)
        serializer = TransactionSerializer(transaction, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a transaction"""
        transaction = self.get_object(pk)
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MarkTransactionAsCompletedView(BaseAPIView):
    """Mark a transaction as completed"""
    permission_classes = [IsAgentPermission | permissions.IsAdminUser]

    def post(self, request, pk, format=None):
        """Mark transaction as completed"""
        transaction = get_object_or_404(Transaction, pk=pk)

        # Mark as completed
        success = transaction.mark_as_completed(processor=request.user)

        if success:
            return Response({'status': 'Transaction marked as completed'})
        return Response(
            {'error': 'Failed to mark transaction as completed'},
            status=status.HTTP_400_BAD_REQUEST
        )



class MarkTransactionAsFailedView(BaseAPIView):
    """Mark a transaction as failed"""
    permission_classes = [IsAgentPermission | permissions.IsAdminUser]

    def post(self, request, pk, format=None):
        """Mark transaction as failed with reason"""
        transaction = get_object_or_404(Transaction, pk=pk)
        reason = request.data.get('reason')

        # Mark as failed
        success = transaction.mark_as_failed(reason=reason)

        if success:
            return Response({'status': 'Transaction marked as failed'})
        return Response(
            {'error': 'Failed to mark transaction as failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


class MyTransactionsView(BaseAPIView):
    """List transactions the user is involved with"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's transactions"""
        user = request.user
        transactions = Transaction.objects.filter(
            Q(from_user=user) |
            Q(to_user=user)
        )

        # Filter by type
        transaction_type = request.query_params.get('transaction_type')
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)

        # Filter by direction
        direction = request.query_params.get('direction')
        if direction == 'incoming':
            transactions = transactions.filter(to_user=user)
        elif direction == 'outgoing':
            transactions = transactions.filter(from_user=user)

        # Handle pagination
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


# Notification Views
class NotificationListCreateView(BaseAPIView):
    """List and create notifications"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAdminUser | IsAgentPermission],
    }

    def get_queryset(self):
        """Get filtered notification queryset"""
        queryset = Notification.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter for non-staff users
        if not user.is_staff:
            queryset = queryset.filter(recipient=user)

        # Filter by read status
        is_read = params.get('is_read')
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)

        # Filter by notification type
        notification_type = params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Apply ordering
        ordering = params.get('ordering')
        if ordering and ordering.lstrip('-') in ['created_at', 'sent_at', 'read_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get(self, request, format=None):
        """List notifications"""
        queryset = self.get_queryset()

        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NotificationSerializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    @transaction.atomic
    def post(self, request, format=None):
        """Create a notification"""
        serializer = NotificationSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors, 'validation_error')

        try:
            notification = serializer.save()
            return self.success_response(
                data=serializer.data,
                message='Notification created successfully',
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return self.error_response('Failed to create notification', 'creation_error',
                                      status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationDetailView(BaseAPIView):
    """Retrieve, update and delete a notification"""
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAdminUser],
        'patch': [permissions.IsAdminUser],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get notification with permission check"""
        user = self.request.user

        # Regular users can only access their own notifications
        if user.is_staff:
            queryset = Notification.objects.all()
        else:
            queryset = Notification.objects.filter(recipient=user)

        notification = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, notification)
        return notification

    def get(self, request, pk, format=None):
        """Retrieve a notification"""
        notification = self.get_object(pk)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a notification"""
        notification = self.get_object(pk)
        serializer = NotificationSerializer(notification, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a notification"""
        notification = self.get_object(pk)
        serializer = NotificationSerializer(notification, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a notification"""
        notification = self.get_object(pk)
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarkNotificationAsReadView(BaseAPIView):
    """Mark a notification as read"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Mark notification as read"""
        try:
            notification = get_object_or_404(Notification, pk=pk)
            user = request.user

            # Ensure user is the recipient
            if notification.recipient != user and not user.is_staff:
                return self.permission_denied('You are not the recipient of this notification')

            # Check if already read
            if notification.is_read:
                return self.success_response(message='Notification already marked as read')

            # Mark as read
            success = notification.mark_as_read()

            if success:
                return self.success_response(message='Notification marked as read')

            return self.error_response('Failed to mark notification as read', 'marking_failed')
        except Http404:
            return self.not_found('Notification not found')
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return self.error_response('An error occurred', 'marking_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarkAllNotificationsAsReadView(BaseAPIView):
    """Mark all notifications as read for the current user"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, format=None):
        """Mark all notifications as read"""
        try:
            user = request.user
            count = Notification.objects.filter(
                recipient=user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )

            return self.success_response(message=f'{count} notifications marked as read')
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return self.error_response('Failed to mark notifications as read', 'bulk_marking_error',
                                     status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyNotificationsView(BaseAPIView):
    """List notifications for the current user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get user's notifications"""
        user = request.user
        notifications = Notification.objects.filter(recipient=user)

        # Filter by read status
        read_status = request.query_params.get('is_read')
        if read_status is not None:
            is_read = read_status.lower() == 'true'
            notifications = notifications.filter(is_read=is_read)

        # Filter by type
        notification_type = request.query_params.get('notification_type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)

        # Handle pagination
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
