import logging
from rest_framework import permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models, transaction
from django.db.models import F, Q, Exists, OuterRef, Subquery
from django.http import Http404
from .permissions import *
from .utils import create_response
from accounts.models import Role, CustomUser
from .models import *
from .decorators import (
    debug_request,
    handle_exceptions,
    cache_view,
    CACHE_SHORT,
    CACHE_MEDIUM,
    CACHE_LONG,
    timer,
    role_required,
    with_cache
)
from .serializers import *
from rest_framework.exceptions import PermissionDenied

# Configure logger
logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    """
    Base APIView that implements common permission logic and consistent error handling.
    """
    # Default permission is to require authentication
    permission_classes = [permissions.IsAuthenticated]

    # Map actions to required permissions
    # By default, allow authenticated users for safe methods, but require staff for others
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAdminUser],
        'put': [permissions.IsAdminUser],
        'patch': [permissions.IsAdminUser],
        'delete': [permissions.IsAdminUser],
    }

    @handle_exceptions
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to apply handle_exceptions decorator to all actions.
        """
        return super().dispatch(request, *args, **kwargs)

    def get_permissions(self):
        """
        Override to get permissions for the current HTTP method.
        """
        method = self.request.method.lower()
        if method in self.action_permission_map:
            return [permission() for permission in self.action_permission_map[method]]
        return [permission() for permission in self.permission_classes]

    # Adds pagination capability
    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            self._paginator = PageNumberPagination()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    # Helper methods for standardized responses
    def error_response(self, error, error_code=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Create a standardized error response."""
        return create_response(
            error=error,
            error_code=error_code,
            status_code=status_code
        )

    def success_response(self, data=None, message=None, status_code=status.HTTP_200_OK):
        """Create a standardized success response."""
        return create_response(
            data=data,
            message=message,
            status_code=status_code
        )

    def permission_denied(self, message="You don't have permission to perform this action"):
        """Create a permission denied response."""
        return self.error_response(
            error=message,
            error_code="permission_denied",
            status_code=status.HTTP_403_FORBIDDEN
        )

    def not_found(self, message="Resource not found"):
        """Create a not found response."""
        return self.error_response(
            error=message,
            error_code="not_found",
            status_code=status.HTTP_404_NOT_FOUND
        )



class BaseUploadView(BaseAPIView):
    """
    Base API view for file uploads that implements common functionality.
    """
    permission_classes = [permissions.IsAuthenticated]

    # Model class to which the uploaded file will be attached (override in subclasses)
    model_class = None

    # Field name for the file field in the model (override in subclasses)
    file_field_name = None

    # Permission class for checking if user can upload to this object (override in subclasses)
    object_permission_class = None

    # Whether to allow multiple files (override in subclasses)
    allow_multiple = False

    # Allowed file extensions (override in subclasses)
    allowed_extensions = None

    # Maximum file size in bytes (override in subclasses)
    max_file_size = 10 * 1024 * 1024  # 10MB by default

    def get_object(self, pk):
        """Get the object to which files will be uploaded"""
        obj = get_object_or_404(self.model_class, pk=pk)

        # Check if the user has permission to upload files to this object
        if self.object_permission_class:
            permission = self.object_permission_class()
            if not permission.has_object_permission(self.request, self, obj):
                raise PermissionDenied("You don't have permission to upload files to this object")

        return obj

    def validate_file(self, file):
        """Validate file size and extension"""
        # Check file size
        if file.size > self.max_file_size:
            return False, f"File size exceeds the limit of {self.max_file_size / (1024 * 1024)}MB"

        # Check file extension if specified
        if self.allowed_extensions:
            ext = file.name.split('.')[-1].lower()
            if ext not in self.allowed_extensions:
                return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"

        return True, None

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Handle file upload"""
        try:
            obj = self.get_object(pk)

            # Check if files were provided
            if 'file' not in request.FILES and 'files' not in request.FILES:
                return self.error_response(
                    'No files were submitted',
                    'no_files_error',
                    status.HTTP_400_BAD_REQUEST
                )

            # Handle multiple file uploads
            if self.allow_multiple and 'files' in request.FILES:
                files = request.FILES.getlist('files')

                # Validate all files first
                for file in files:
                    is_valid, error_msg = self.validate_file(file)
                    if not is_valid:
                        return self.error_response(
                            error_msg,
                            'file_validation_error',
                            status.HTTP_400_BAD_REQUEST
                        )

                # Process all files
                uploaded_files = []
                for file in files:
                    # Get or create the file field if it's a many-to-many relationship
                    if hasattr(obj, self.file_field_name):
                        field = getattr(obj, self.file_field_name)
                        if hasattr(field, 'create'):  # It's a related manager
                            uploaded_file = field.create(
                                file=file,
                                uploaded_by=request.user,
                                file_name=file.name,
                                file_size=file.size,
                                file_type=file.content_type
                            )
                        else:  # It's a direct field or a foreign key
                            setattr(obj, self.file_field_name, file)
                            obj.save()
                            uploaded_file = getattr(obj, self.file_field_name)

                    uploaded_files.append(uploaded_file)

                return self.success_response(
                    message=f"{len(uploaded_files)} files uploaded successfully",
                    status_code=status.HTTP_201_CREATED
                )

            # Handle single file upload
            else:
                file = request.FILES.get('file')
                if not file:
                    file = request.FILES.get('files')[0]  # Get first file if multiple were sent

                # Validate the file
                is_valid, error_msg = self.validate_file(file)
                if not is_valid:
                    return self.error_response(
                        error_msg,
                        'file_validation_error',
                        status.HTTP_400_BAD_REQUEST
                    )

                # Set the file field
                if hasattr(obj, self.file_field_name):
                    field = getattr(obj, self.file_field_name)
                    if hasattr(field, 'create'):  # It's a related manager
                        uploaded_file = field.create(
                            file=file,
                            uploaded_by=request.user,
                            file_name=file.name,
                            file_size=file.size,
                            file_type=file.content_type
                        )
                    else:  # It's a direct field or a foreign key
                        setattr(obj, self.file_field_name, file)
                        obj.save()
                        uploaded_file = getattr(obj, self.file_field_name)

                return self.success_response(
                    message="File uploaded successfully",
                    status_code=status.HTTP_201_CREATED
                )

        except Http404:
            return self.not_found(f"{self.model_class.__name__} not found")
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return self.error_response(
                f"An error occurred while uploading the file: {str(e)}",
                'upload_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class PropertyListCreateView(BaseAPIView):
    """
    API view for listing and creating properties.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [IsSellerPermission],
    }

    def _apply_filters(self, queryset):
        """Apply filters from query parameters to the queryset."""
        params = self.request.query_params
        user = self.request.user

        # Filter by published status for non-staff users
        if not user.is_staff:
            queryset = queryset.filter(is_published=True)

        # Apply simple field filters
        filter_fields = {
            'status': params.get('status'),
            'property_type': params.get('property_type'),
            'city': params.get('city'),
            'district': params.get('district'),
            'bedrooms': params.get('bedrooms'),
            'bathrooms': params.get('bathrooms'),
        }

        for field, value in filter_fields.items():
            if value:
                queryset = queryset.filter(**{field: value})

        # Apply search if provided
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(address__icontains=search) |
                Q(property_number__icontains=search)
            )

        # Apply ordering if provided
        ordering = params.get('ordering')
        if ordering:
            # Get field name without the possible '-' prefix
            field = ordering[1:] if ordering.startswith('-') else ordering
            allowed_fields = ['created_at', 'estimated_value', 'area', 'views_count']

            if field in allowed_fields:
                queryset = queryset.order_by(ordering)

        return queryset

    def get_queryset(self):
        """Customize queryset based on user role and request parameters."""
        return self._apply_filters(Property.objects.all())

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
        """Create a new property"""
        serializer = PropertySerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                'validation_error',
                status.HTTP_400_BAD_REQUEST
            )

        try:
            property_obj = serializer.save(owner=request.user)
            return self.success_response(
                data=serializer.data,
                message='Property created successfully',
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating property: {str(e)}")
            return self.error_response(
                'Failed to create property',
                'creation_failed',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PropertyDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting a property.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [IsPropertyOwner],
        'patch': [IsPropertyOwner],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get property by primary key"""
        property = get_object_or_404(Property, pk=pk)
        self.check_object_permissions(self.request, property)
        return property

    def get(self, request, pk, format=None):
        """Retrieve a property"""
        property = self.get_object(pk)
        serializer = PropertySerializer(property)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update a property"""
        property = self.get_object(pk)
        serializer = PropertySerializer(property, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update a property"""
        property = self.get_object(pk)
        serializer = PropertySerializer(property, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete a property"""
        property = self.get_object(pk)
        property.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyPropertiesView(BaseAPIView):
    """
    API view for listing properties owned by the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """List properties owned by the current user"""
        properties = Property.objects.filter(owner=request.user)

        # Handle pagination
        page = self.paginate_queryset(properties)
        if page is not None:
            serializer = PropertySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PropertySerializer(properties, many=True)
        return Response(serializer.data)


class VerifyPropertyView(BaseAPIView):
    """
    API view for verifying a property.
    """
    permission_classes = [IsInspectorPermission]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Verify a property"""
        property = get_object_or_404(Property, pk=pk)

        # Check if property is already verified
        if property.is_verified:
            return Response({'status': 'property already verified'}, status=status.HTTP_200_OK)

        property.is_verified = True
        property.verified_by = request.user
        property.verification_date = timezone.now()
        property.save(update_fields=['is_verified', 'verified_by', 'verification_date', 'updated_at'])

        return Response({'status': 'property verified'}, status=status.HTTP_200_OK)

class PropertyBySlugView(BaseAPIView):
    """
    API view for retrieving a property by slug.
    """
    permission_classes = [permissions.IsAuthenticated]

    @debug_request
    @cache_view(timeout=CACHE_MEDIUM, key_prefix='property_slug', vary_on_user=False)
    def get(self, request, slug, format=None):
        """Retrieve a property by slug"""
        try:
            # Filter properties based on user permissions
            queryset = Property.objects.all()
            if not request.user.is_staff:
                queryset = queryset.filter(is_published=True)

            # Try to get the property
            property_obj = get_object_or_404(queryset, slug=slug)

            # Increment views count atomically to avoid race conditions
            with transaction.atomic():
                Property.objects.filter(pk=property_obj.pk).update(views_count=F('views_count') + 1)
                # Refresh the object to get updated views_count
                property_obj.refresh_from_db()

            serializer = PropertySerializer(property_obj)
            return self.success_response(data=serializer.data)

        except Http404:
            return self.not_found(f"Property with slug '{slug}' not found")
        except Exception as e:
            logger.error(f"Error retrieving property by slug '{slug}': {str(e)}")
            return self.error_response(
                "An error occurred while retrieving the property",
                "property_retrieval_error",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UploadPropertyImagesView(BaseUploadView):
    """
    API view for uploading images to a property.
    """
    model_class = Property
    file_field_name = 'images'
    object_permission_class = IsPropertyOwner
    allow_multiple = True
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    max_file_size = 5 * 1024 * 1024  # 5MB

# AUCTION VIEWS
class AuctionListCreateView(BaseAPIView):
    """
    API view for listing and creating auctions.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [IsSellerPermission | IsAgentPermission],
    }

    def get_queryset(self):
        """
        Customize queryset based on user role and request parameters.
        """
        queryset = Auction.objects.all()

        # For non-staff users, filter out private auctions they're not invited to
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(
                # Public auctions OR private auctions where user is invited
                (models.Q(is_private=False) |
                 models.Q(is_private=True, invited_bidders=user))
            )

            # Ensure they're published
            queryset = queryset.filter(is_published=True)

        # Apply filtering
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        auction_type = self.request.query_params.get('auction_type', None)
        if auction_type:
            queryset = queryset.filter(auction_type=auction_type)

        is_featured = self.request.query_params.get('is_featured', None)
        if is_featured is not None:
            is_featured_bool = is_featured.lower() == 'true'
            queryset = queryset.filter(is_featured=is_featured_bool)

        is_published = self.request.query_params.get('is_published', None)
        if is_published is not None:
            is_published_bool = is_published.lower() == 'true'
            queryset = queryset.filter(is_published=is_published_bool)

        # Apply search if provided
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # Apply ordering if provided
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if ordering in ['start_date', 'end_date', 'current_bid', 'views_count',
                           '-start_date', '-end_date', '-current_bid', '-views_count']:
                queryset = queryset.order_by(ordering)

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
        """Create a new auction"""
        serializer = AuctionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                created_by=request.user,
                # If no auctioneer is specified, use current user
                auctioneer=serializer.validated_data.get('auctioneer', request.user)
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuctionDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting an auction.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [IsAuctionCreator],
        'patch': [IsAuctionCreator],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get auction by primary key"""
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


class MyAuctionsView(BaseAPIView):
    """
    API view for listing auctions created by or featuring the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """List auctions created by or featuring the current user"""
        auctions = Auction.objects.filter(
            models.Q(created_by=request.user) |
            models.Q(auctioneer=request.user) |
            models.Q(invited_bidders=request.user)
        ).distinct()

        # Handle pagination
        page = self.paginate_queryset(auctions)
        if page is not None:
            serializer = AuctionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AuctionSerializer(auctions, many=True)
        return Response(serializer.data)



class ExtendAuctionView(BaseAPIView):
    """
    API view for extending an auction.
    """
    permission_classes = [IsAuctionCreator]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Extend auction end time"""
        try:
            auction = get_object_or_404(Auction, pk=pk)
            minutes = request.data.get('minutes', auction.extension_minutes)

            # Validate auction status
            if auction.status not in ['active', 'extended']:
                return self.error_response(
                    'Only active or extended auctions can be extended',
                    'invalid_auction_status',
                    status.HTTP_400_BAD_REQUEST
                )

            # Use model method to extend (it handles status changes and notifications)
            success = auction.extend_auction(minutes=minutes)

            if success:
                return self.success_response(
                    message=f'Auction extended by {minutes} minutes'
                )

            return self.error_response(
                'Failed to extend auction',
                'extension_failed',
                status.HTTP_400_BAD_REQUEST
            )

        except Http404:
            return self.not_found('Auction not found')
        except Exception as e:
            logger.error(f"Error extending auction: {str(e)}")
            return self.error_response(
                'An error occurred while extending the auction',
                'extension_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CloseAuctionView(BaseAPIView):
    """
    API view for closing an auction.
    """
    permission_classes = [IsAuctionCreator]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Close an auction before its end time"""
        try:
            auction = get_object_or_404(Auction, pk=pk)

            # Validate auction status
            if auction.status not in ['active', 'extended']:
                return self.error_response(
                    f'Only active or extended auctions can be closed',
                    'invalid_auction_status',
                    status.HTTP_400_BAD_REQUEST
                )

            # Check if auction has already ended naturally
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

            return self.success_response(
                message='Auction closed successfully'
            )

        except Http404:
            return self.not_found('Auction not found')
        except Exception as e:
            logger.error(f"Error closing auction: {str(e)}")
            return self.error_response(
                'An error occurred while closing the auction',
                'closure_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuctionBySlugView(BaseAPIView):
    """
    API view for retrieving an auction by slug.
    """
    permission_classes = [permissions.IsAuthenticated]

    @debug_request
    @cache_view(timeout=CACHE_SHORT, key_prefix='auction_slug', vary_on_user=True)
    def get(self, request, slug, format=None):
        """Retrieve an auction by slug"""
        # Get auctions the user can access
        user = request.user

        if user.is_staff:
            queryset = Auction.objects.all()
        else:
            queryset = Auction.objects.filter(
                # Public auctions OR private auctions where user is invited
                (models.Q(is_private=False) |
                 models.Q(is_private=True, invited_bidders=user))
            )

        auction = get_object_or_404(queryset, slug=slug)

        # Increment views count atomically to avoid race conditions
        with transaction.atomic():
            Auction.objects.filter(pk=auction.pk).update(views_count=F('views_count') + 1)
            # Refresh the object to get updated views_count
            auction.refresh_from_db()

        serializer = AuctionSerializer(auction)
        return Response(serializer.data)

class UploadAuctionImagesView(BaseUploadView):
    """
    API view for uploading images to an auction.
    """
    model_class = Auction
    file_field_name = 'images'
    object_permission_class = IsAuctionCreator
    allow_multiple = True
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    max_file_size = 5 * 1024 * 1024  # 5MB





class PlaceBidView(BaseAPIView):
    """
    API view for placing a bid on an auction.
    """
    permission_classes = [permissions.IsAuthenticated]

    def validate_bid(self, auction, user, bid_amount):
        """
        Validate bid parameters before processing.

        Returns:
            tuple: (is_valid, error_message, error_code, status_code)
        """
        # Check if auction is active
        if auction.status != 'active':
            return False, 'Cannot place bid on inactive auction', 'inactive_auction', status.HTTP_400_BAD_REQUEST

        # Check if auction is in progress time-wise
        now = timezone.now()
        if now < auction.start_date or now > auction.end_date:
            return False, 'Auction is not open for bids at this time', 'auction_closed', status.HTTP_400_BAD_REQUEST

        # Check if private auction and user is invited
        if auction.is_private and user not in auction.invited_bidders.all():
            return False, 'You are not invited to this private auction', 'not_invited', status.HTTP_403_FORBIDDEN

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
        """Place a bid on an auction"""
        try:
            auction = get_object_or_404(Auction, pk=pk)
        except Http404:
            return self.not_found('Auction not found')

        # Validate bid
        bid_amount = request.data.get('bid_amount')
        is_valid, error_msg, error_code, status_code = self.validate_bid(
            auction, request.user, bid_amount
        )

        if not is_valid:
            return self.error_response(error_msg, error_code, status_code)

        # Create and validate bid
        bid_data = {
            'auction': auction.id,
            'bidder': request.user.id,
            'bid_amount': float(bid_amount),
            'max_bid_amount': request.data.get('max_bid_amount', None),
            'is_auto_bid': bool(request.data.get('max_bid_amount', False)),
        }

        # Use serializer to create bid
        serializer = BidSerializer(data=bid_data)
        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                'validation_error',
                status.HTTP_400_BAD_REQUEST
            )

        # Save the bid
        bid = serializer.save(
            bidder=request.user,
            ip_address=request.META.get('REMOTE_ADDR', None),
            user_agent=request.META.get('HTTP_USER_AGENT', None)
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
    """
    API view for listing and creating bids.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def get_queryset(self):
        """
        Customize queryset based on user role and request parameters.
        """
        queryset = Bid.objects.all()
        user = self.request.user

        # Regular users can only see their own bids or bids for auctions they created/manage
        if not user.is_staff:
            queryset = queryset.filter(
                models.Q(bidder=user) |
                models.Q(auction__created_by=user) |
                models.Q(auction__auctioneer=user)
            )

        # Filter by auction if specified
        auction_id = self.request.query_params.get('auction_id', None)
        if auction_id:
            queryset = queryset.filter(auction_id=auction_id)

        # Apply filtering
        auction = self.request.query_params.get('auction', None)
        if auction:
            queryset = queryset.filter(auction=auction)

        bidder = self.request.query_params.get('bidder', None)
        if bidder:
            queryset = queryset.filter(bidder=bidder)

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        is_auto_bid = self.request.query_params.get('is_auto_bid', None)
        if is_auto_bid is not None:
            is_auto_bid_bool = is_auto_bid.lower() == 'true'
            queryset = queryset.filter(is_auto_bid=is_auto_bid_bool)

        # Apply ordering if provided
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if ordering in ['bid_amount', 'bid_time', '-bid_amount', '-bid_time']:
                queryset = queryset.order_by(ordering)

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
        """Create a new bid"""
        serializer = BidSerializer(data=request.data)
        if serializer.is_valid():
            # Get the auction to verify permissions
            auction = serializer.validated_data.get('auction')
            user = request.user

            # Verify user can bid on this auction
            if auction.is_private and user not in auction.invited_bidders.all():
                return Response(
                    {"detail": "You are not invited to this private auction"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Set bid metadata
            ip_address = request.META.get('REMOTE_ADDR', None)
            user_agent = request.META.get('HTTP_USER_AGENT', None)

            bid = serializer.save(
                bidder=user,
                ip_address=ip_address,
                user_agent=user_agent
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BidDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting a bid.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAdminUser],
        'patch': [permissions.IsAdminUser],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get bid by primary key"""
        user = self.request.user

        # Regular users can only see their own bids or bids for auctions they created/manage
        if user.is_staff:
            queryset = Bid.objects.all()
        else:
            queryset = Bid.objects.filter(
                models.Q(bidder=user) |
                models.Q(auction__created_by=user) |
                models.Q(auction__auctioneer=user)
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
    """
    API view for listing bids placed by the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """List bids placed by the current user"""
        bids = Bid.objects.filter(bidder=request.user)

        # Allow filtering by auction
        auction_id = request.query_params.get('auction_id', None)
        if auction_id:
            bids = bids.filter(auction_id=auction_id)

        # Handle pagination
        page = self.paginate_queryset(bids)
        if page is not None:
            serializer = BidSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BidSerializer(bids, many=True)
        return Response(serializer.data)



# DOCUMENT VIEWS
class DocumentListCreateView(BaseAPIView):
    """
    API view for listing and creating documents.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def get_queryset(self):
        """
        Customize queryset based on user role and request parameters.
        """
        queryset = Document.objects.all()
        user = self.request.user

        # Non-staff users can only see documents they uploaded or documents
        # related to their properties, auctions, or contracts
        if not user.is_staff:
            queryset = queryset.filter(
                models.Q(uploaded_by=user) |
                models.Q(related_property__owner=user) |
                models.Q(auction__created_by=user) |
                models.Q(auction__auctioneer=user) |
                models.Q(contract__buyer=user) |
                models.Q(contract__seller=user) |
                models.Q(contract__agent=user)
            )

        # Apply filtering
        document_type = self.request.query_params.get('document_type', None)
        if document_type:
            queryset = queryset.filter(document_type=document_type)

        verification_status = self.request.query_params.get('verification_status', None)
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)

        related_property = self.request.query_params.get('related_property', None)
        if related_property:
            queryset = queryset.filter(related_property=related_property)

        auction = self.request.query_params.get('auction', None)
        if auction:
            queryset = queryset.filter(auction=auction)

        contract = self.request.query_params.get('contract', None)
        if contract:
            queryset = queryset.filter(contract=contract)

        # Apply search if provided
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(document_number__icontains=search)
            )

        # Apply ordering if provided
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if ordering in ['created_at', 'issue_date', 'expiry_date',
                           '-created_at', '-issue_date', '-expiry_date']:
                queryset = queryset.order_by(ordering)

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
        """Create a new document"""
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting a document.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAuthenticated],
        'patch': [permissions.IsAuthenticated],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get document by primary key"""
        document = get_object_or_404(Document, pk=pk)
        self.check_object_permissions(self.request, document)

        # Additional permission check for update actions
        if self.request.method in ['PUT', 'PATCH']:
            user = self.request.user
            if user != document.uploaded_by and not user.is_staff and not user.has_role(Role.LEGAL):
                from rest_framework.exceptions import PermissionDenied
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



class MarkBidAsWinningView(BaseAPIView):
    """
    API view for marking a bid as the winning bid.
    """
    permission_classes = [IsAgentPermission]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Mark a bid as the winning bid"""
        try:
            bid = get_object_or_404(Bid, pk=pk)
            auction = bid.auction

            # Verify user is authorized to mark winner
            user = request.user
            if not user.is_staff and user != auction.created_by and user != auction.auctioneer:
                return self.permission_denied('You do not have permission to mark the winning bid')

            # Check auction status
            if auction.status not in ['closed', 'extended', 'active']:
                return self.error_response(
                    f'Cannot mark winning bid for auction with status {auction.status}',
                    'invalid_auction_status',
                    status.HTTP_400_BAD_REQUEST
                )

            # Check if auction already has a winning bid
            if auction.winning_bidder is not None:
                return self.error_response(
                    'This auction already has a winning bid',
                    'winner_exists',
                    status.HTTP_400_BAD_REQUEST
                )

            # Use model method to mark as winning
            success = bid.mark_as_winning()

            if success:
                return self.success_response(
                    message='Bid marked as winning successfully'
                )

            return self.error_response(
                'Failed to mark bid as winning',
                'marking_failed',
                status.HTTP_400_BAD_REQUEST
            )

        except Http404:
            return self.not_found('Bid not found')
        except Exception as e:
            logger.error(f"Error marking bid as winning: {str(e)}")
            return self.error_response(
                'An error occurred while marking the winning bid',
                'marking_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyDocumentView(BaseAPIView):
    """
    API view for verifying a document.
    """
    permission_classes = [IsLegalPermission | IsInspectorPermission]

    def post(self, request, pk, format=None):
        """Verify a document"""
        document = get_object_or_404(Document, pk=pk)
        notes = request.data.get('notes', None)

        # Execute verification
        success = document.verify(user=request.user, notes=notes)

        if success:
            return Response({'status': 'document verified'}, status=status.HTTP_200_OK)
        return Response(
            {'error': 'Failed to verify document'},
            status=status.HTTP_400_BAD_REQUEST
        )


class MyDocumentsView(BaseAPIView):
    """
    API view for listing documents uploaded by the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """List documents uploaded by the current user"""
        documents = Document.objects.filter(uploaded_by=request.user)

        # Allow filtering
        doc_type = request.query_params.get('document_type', None)
        if doc_type:
            documents = documents.filter(document_type=doc_type)

        # Handle pagination
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = DocumentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)

class UploadDocumentFilesView(BaseUploadView):
    """
    API view for uploading files to a document.
    """
    model_class = Document
    file_field_name = 'files'
    allow_multiple = True
    allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
    max_file_size = 10 * 1024 * 1024  # 10MB

    def get_object(self, pk):
        """Get document by primary key with additional permissions check"""
        document = get_object_or_404(Document, pk=pk)

        # Check if user has permission to upload files to this document
        user = self.request.user
        if (user != document.uploaded_by and
            not user.is_staff and
            not user.has_role(Role.LEGAL) and
            not (document.related_property and document.related_property.owner == user) and
            not (document.auction and document.auction.created_by == user) and
            not (document.contract and (document.contract.buyer == user or
                                       document.contract.seller == user or
                                       document.contract.agent == user))):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to upload files to this document")

        return document

# CONTRACT VIEWS
class ContractListCreateView(BaseAPIView):
    """
    API view for listing and creating contracts.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [IsLegalPermission | IsAgentPermission],
    }

    def get_queryset(self):
        """
        Customize queryset based on user role and request parameters.
        """
        queryset = Contract.objects.all()
        user = self.request.user

        # For non-staff users, filter to show only contracts they're involved in
        if not user.is_staff:
            queryset = queryset.filter(
                models.Q(buyer=user) |
                models.Q(seller=user) |
                models.Q(agent=user) |
                models.Q(auction__created_by=user) |
                models.Q(auction__auctioneer=user)
            )

        # Apply filtering
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        contract_date = self.request.query_params.get('contract_date', None)
        if contract_date:
            queryset = queryset.filter(contract_date=contract_date)

        buyer = self.request.query_params.get('buyer', None)
        if buyer:
            queryset = queryset.filter(buyer=buyer)

        seller = self.request.query_params.get('seller', None)
        if seller:
            queryset = queryset.filter(seller=seller)

        agent = self.request.query_params.get('agent', None)
        if agent:
            queryset = queryset.filter(agent=agent)

        related_property = self.request.query_params.get('related_property', None)
        if related_property:
            queryset = queryset.filter(related_property=related_property)

        auction = self.request.query_params.get('auction', None)
        if auction:
            queryset = queryset.filter(auction=auction)

        # Apply search if provided
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(contract_number__icontains=search)
            )

        # Apply ordering if provided
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if ordering in ['created_at', 'contract_date', 'effective_date', 'contract_amount',
                           '-created_at', '-contract_date', '-effective_date', '-contract_amount']:
                queryset = queryset.order_by(ordering)

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
        """Create a new contract"""
        serializer = ContractSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContractDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting a contract.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [IsLegalPermission | IsAgentPermission],
        'patch': [IsLegalPermission | IsAgentPermission],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get contract by primary key"""
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


class UploadContractFilesView(BaseUploadView):
    """
    API view for uploading files to a contract.
    """
    model_class = Contract
    file_field_name = 'files'
    allow_multiple = True
    allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
    max_file_size = 10 * 1024 * 1024  # 10MB

    def get_object(self, pk):
        """Get contract by primary key with additional permissions check"""
        contract = get_object_or_404(Contract, pk=pk)

        # Check if user has permission to upload files to this contract
        user = self.request.user
        if (not user.is_staff and
            not user.has_role(Role.LEGAL) and
            not user.has_role(Role.AGENT) and
            user != contract.buyer and
            user != contract.seller and
            user != contract.agent):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to upload files to this contract")

        return contract




class SignContractAsBuyerView(BaseAPIView):
    """
    API view for signing a contract as buyer.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Sign contract as buyer"""
        try:
            contract = get_object_or_404(Contract, pk=pk)
            user = request.user

            # Verify current user is the buyer
            if user != contract.buyer:
                return self.permission_denied('You are not the buyer for this contract')

            # Check if already signed
            if contract.buyer_signed:
                return self.success_response(
                    message='Contract already signed by buyer'
                )

            # Use model method to sign (it handles status updates)
            success = contract.sign_as_buyer(user=user)

            if success:
                return self.success_response(
                    message='Contract signed successfully'
                )

            return self.error_response(
                'Failed to sign contract',
                'signing_failed',
                status.HTTP_400_BAD_REQUEST
            )

        except Http404:
            return self.not_found('Contract not found')
        except Exception as e:
            logger.error(f"Error signing contract as buyer: {str(e)}")
            return self.error_response(
                'An error occurred while signing the contract',
                'signing_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SignContractAsSellerView(BaseAPIView):
    """
    API view for signing a contract as seller.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Sign contract as seller"""
        try:
            contract = get_object_or_404(Contract, pk=pk)
            user = request.user

            # Verify current user is the seller
            if user != contract.seller:
                return self.permission_denied('You are not the seller for this contract')

            # Check if already signed
            if contract.seller_signed:
                return self.success_response(
                    message='Contract already signed by seller'
                )

            # Use model method to sign (it handles status updates)
            success = contract.sign_as_seller(user=user)

            if success:
                return self.success_response(
                    message='Contract signed successfully'
                )

            return self.error_response(
                'Failed to sign contract',
                'signing_failed',
                status.HTTP_400_BAD_REQUEST
            )

        except Http404:
            return self.not_found('Contract not found')
        except Exception as e:
            logger.error(f"Error signing contract as seller: {str(e)}")
            return self.error_response(
                'An error occurred while signing the contract',
                'signing_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SignContractAsAgentView(BaseAPIView):
    """
    API view for signing a contract as agent.
    """
    permission_classes = [IsAgentPermission]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Sign contract as agent"""
        try:
            contract = get_object_or_404(Contract, pk=pk)
            user = request.user

            # Verify current user is the agent
            if user != contract.agent:
                return self.permission_denied('You are not the agent for this contract')

            # Check if already signed
            if contract.agent_signed:
                return self.success_response(
                    message='Contract already signed by agent'
                )

            # Sign as agent
            contract.agent_signed = True
            contract.agent_signature_date = timezone.now()

            # Update status if both buyer and seller have signed
            if contract.buyer_signed and contract.seller_signed:
                contract.status = 'signed'

            contract.save(update_fields=[
                'agent_signed', 'agent_signature_date', 'status', 'updated_at'
            ])

            return self.success_response(
                message='Contract signed successfully'
            )

        except Http404:
            return self.not_found('Contract not found')
        except Exception as e:
            logger.error(f"Error signing contract as agent: {str(e)}")
            return self.error_response(
                'An error occurred while signing the contract',
                'signing_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class MyContractsView(BaseAPIView):
    """
    API view for listing contracts the current user is involved with.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """List contracts the current user is involved with"""
        user = request.user
        contracts = Contract.objects.filter(
            models.Q(buyer=user) |
            models.Q(seller=user) |
            models.Q(agent=user)
        )

        # Additional filtering
        status_filter = request.query_params.get('status', None)
        if status_filter:
            contracts = contracts.filter(status=status_filter)

        # Handle pagination
        page = self.paginate_queryset(contracts)
        if page is not None:
            serializer = ContractSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ContractSerializer(contracts, many=True)
        return Response(serializer.data)


class PaymentListCreateView(BaseAPIView):
    """
    API view for listing and creating payments.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def _apply_filters(self, queryset):
        """Apply filters from query parameters to the queryset."""
        params = self.request.query_params
        user = self.request.user

        # Filter based on user permissions
        if not user.is_staff and not user.has_role(Role.AGENT):
            queryset = queryset.filter(
                models.Q(payer=user) |
                models.Q(payee=user) |
                models.Q(contract__buyer=user) |
                models.Q(contract__seller=user) |
                models.Q(contract__agent=user)
            )

        # Apply simple field filters
        filter_fields = {
            'status': params.get('status'),
            'payment_type': params.get('payment_type'),
            'payment_method': params.get('payment_method'),
            'contract': params.get('contract'),
            'payer': params.get('payer'),
            'payee': params.get('payee'),
        }

        for field, value in filter_fields.items():
            if value:
                queryset = queryset.filter(**{field: value})

        # Apply search if provided
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(payment_number__icontains=search) |
                Q(transaction_reference__icontains=search)
            )

        # Apply ordering if provided
        ordering = params.get('ordering')
        if ordering:
            allowed_orderings = [
                'payment_date', 'amount', 'created_at',
                '-payment_date', '-amount', '-created_at'
            ]
            if ordering in allowed_orderings:
                queryset = queryset.order_by(ordering)

        return queryset

    def get_queryset(self):
        """Get filtered queryset."""
        return self._apply_filters(Payment.objects.all())

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
        """Create a new payment"""
        serializer = PaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                'validation_error',
                status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = serializer.save(payer=request.user)
            return self.success_response(
                data=serializer.data,
                message='Payment created successfully',
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            return self.error_response(
                'Failed to create payment',
                'creation_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting a payment.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAdminUser | IsAgentPermission],
        'patch': [permissions.IsAdminUser | IsAgentPermission],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get payment by primary key"""
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
    """
    API view for confirming a payment.
    """
    permission_classes = [IsAgentPermission]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Confirm a payment"""
        try:
            payment = get_object_or_404(Payment, pk=pk)

            # Check if payment is already confirmed
            if payment.status == 'completed':
                return self.success_response(
                    message='Payment already confirmed'
                )

            # Verify payment status allows confirmation
            if payment.status not in ['pending', 'processing']:
                return self.error_response(
                    f'Cannot confirm payment with status {payment.status}',
                    'invalid_payment_status',
                    status.HTTP_400_BAD_REQUEST
                )

            # Use model method to confirm payment (it handles contract updates)
            success = payment.confirm_payment(user=request.user)

            if success:
                return self.success_response(
                    message='Payment confirmed successfully'
                )

            return self.error_response(
                'Failed to confirm payment',
                'confirmation_failed',
                status.HTTP_400_BAD_REQUEST
            )

        except Http404:
            return self.not_found('Payment not found')
        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}")
            return self.error_response(
                'An error occurred while confirming the payment',
                'confirmation_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MyPaymentsView(BaseAPIView):
    """
    API view for listing payments made or received by the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """List payments made or received by the current user"""
        user = request.user
        payments = Payment.objects.filter(
            models.Q(payer=user) |
            models.Q(payee=user)
        )

        # Filter by type
        payment_type = request.query_params.get('payment_type', None)
        if payment_type:
            payments = payments.filter(payment_type=payment_type)

        # Filter by direction (made/received)
        direction = request.query_params.get('direction', None)
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

class UploadPaymentReceiptView(BaseUploadView):
    """
    API view for uploading receipt to a payment.
    """
    model_class = Payment
    file_field_name = 'receipt'
    allow_multiple = False
    allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
    max_file_size = 5 * 1024 * 1024  # 5MB

    def get_object(self, pk):
        """Get payment by primary key with additional permissions check"""
        payment = get_object_or_404(Payment, pk=pk)

        # Check if user has permission to upload receipt for this payment
        user = self.request.user
        if user != payment.payer and not user.is_staff and not user.has_role(Role.AGENT):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to upload receipt for this payment")

        return payment



# MESSAGE THREAD VIEWS
class MessageThreadListCreateView(BaseAPIView):
    """
    API view for listing and creating message threads.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def get_queryset(self):
        """
        Customize queryset based on user role and request parameters.
        """
        queryset = MessageThread.objects.all()
        user = self.request.user

        # Non-staff users can only see threads they're participating in
        if not user.is_staff:
            queryset = queryset.filter(
                thread_participants__user=user,
                thread_participants__is_active=True
            )

        # Apply filtering
        thread_type = self.request.query_params.get('thread_type', None)
        if thread_type:
            queryset = queryset.filter(thread_type=thread_type)

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        is_private = self.request.query_params.get('is_private', None)
        if is_private is not None:
            is_private_bool = is_private.lower() == 'true'
            queryset = queryset.filter(is_private=is_private_bool)

        is_system_thread = self.request.query_params.get('is_system_thread', None)
        if is_system_thread is not None:
            is_system_thread_bool = is_system_thread.lower() == 'true'
            queryset = queryset.filter(is_system_thread=is_system_thread_bool)

        creator = self.request.query_params.get('creator', None)
        if creator:
            queryset = queryset.filter(creator=creator)

        # Apply search if provided
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(subject__icontains=search)

        # Apply ordering if provided
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if ordering in ['last_message_at', 'created_at', '-last_message_at', '-created_at']:
                queryset = queryset.order_by(ordering)

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
        """Create a new message thread"""
        serializer = MessageThreadSerializer(data=request.data)
        if serializer.is_valid():
            thread = serializer.save(creator=request.user)

            # Add the creator as a participant
            ThreadParticipant.objects.create(
                thread=thread,
                user=request.user,
                is_active=True
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageThreadDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting a message thread.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAuthenticated],
        'patch': [permissions.IsAuthenticated],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get message thread by primary key"""
        thread = get_object_or_404(MessageThread, pk=pk)
        self.check_object_permissions(self.request, thread)

        # Additional permission check for update actions
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
                from rest_framework.exceptions import PermissionDenied
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


class AddThreadParticipantView(BaseAPIView):
    """
    API view for adding a participant to a thread.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Add a participant to the thread"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check if user has permission to add participants
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
        user_to_add_id = request.data.get('user_id')
        if not user_to_add_id:
            return Response(
                {'error': 'User ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_to_add = CustomUser.objects.get(id=user_to_add_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Add user as participant
        role = request.data.get('role', 'member')
        participant = thread.add_participant(user_to_add, role=role)

        return Response({'status': 'participant added'}, status=status.HTTP_200_OK)


class RemoveThreadParticipantView(BaseAPIView):
    """
    API view for removing a participant from a thread.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Remove a participant from the thread"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check if user has permission to remove participants
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
        user_to_remove_id = request.data.get('user_id')
        if not user_to_remove_id:
            return Response(
                {'error': 'User ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_to_remove = CustomUser.objects.get(id=user_to_remove_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Remove user from thread
        success = thread.remove_participant(user_to_remove)

        if success:
            return Response({'status': 'participant removed'}, status=status.HTTP_200_OK)
        return Response(
            {'error': 'Failed to remove participant'},
            status=status.HTTP_400_BAD_REQUEST
        )


class MarkThreadAsReadView(BaseAPIView):
    """
    API view for marking all messages in a thread as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Mark all messages in thread as read"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check if user is a participant
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

        # Mark thread as read for user
        count = participant.mark_all_as_read()

        return Response({'status': f'{count} messages marked as read'}, status=status.HTTP_200_OK)


class CloseThreadView(BaseAPIView):
    """
    API view for closing a thread.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Close a thread"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check if thread is already closed
        if thread.status == 'closed':
            return Response(
                {'status': 'thread is already closed'},
                status=status.HTTP_200_OK
            )

        # Check permissions to close
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

        return Response({'status': 'thread closed'}, status=status.HTTP_200_OK)


class ReopenThreadView(BaseAPIView):
    """
    API view for reopening a closed thread.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Reopen a closed thread"""
        thread = get_object_or_404(MessageThread, pk=pk)
        user = request.user

        # Check if thread is already active
        if thread.status == 'active':
            return Response(
                {'status': 'thread is already active'},
                status=status.HTTP_200_OK
            )

        # Check permissions to reopen
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

        return Response({'status': 'thread reopened'}, status=status.HTTP_200_OK)


class MyThreadsView(BaseAPIView):
    """
    API view for getting threads the current user is participating in.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get threads the current user is participating in"""
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

            # Filter by unread - More efficient implementation
            unread_only = request.query_params.get('unread', 'false').lower() == 'true'
            if unread_only:
                # Prefetch participants to avoid N+1 queries
                threads = threads.prefetch_related('thread_participants', 'messages')

                # Get participant records for the current user
                participant_subquery = ThreadParticipant.objects.filter(
                    thread=OuterRef('pk'),
                    user=user,
                    is_active=True
                )

                # Annotate threads with the user's last_read_at timestamp
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
                error_code="thread_retrieval_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ThreadBySlugView(BaseAPIView):
    """
    API view for retrieving a message thread by its slug.
    """
    permission_classes = [permissions.IsAuthenticated]

    @debug_request
    @cache_view(timeout=CACHE_SHORT, key_prefix='thread_slug', vary_on_user=True)
    def get(self, request, slug, format=None):
        """Retrieve a message thread by its slug"""
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


# MESSAGE VIEWS
class MessageListCreateView(BaseAPIView):
    """
    API view for listing and creating messages.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAuthenticated],
    }

    def get_queryset(self):
        """
        Customize queryset based on user role and request parameters.
        """
        queryset = Message.objects.all()
        user = self.request.user

        # Non-staff users can only see messages in threads they're participating in
        if not user.is_staff:
            # Get threads the user is participating in
            threads = MessageThread.objects.filter(
                thread_participants__user=user,
                thread_participants__is_active=True
            )
            queryset = queryset.filter(thread__in=threads)

        # Apply filtering
        thread_id = self.request.query_params.get('thread_id', None)
        if thread_id:
            queryset = queryset.filter(thread_id=thread_id)

        thread = self.request.query_params.get('thread', None)
        if thread:
            queryset = queryset.filter(thread=thread)

        sender = self.request.query_params.get('sender', None)
        if sender:
            queryset = queryset.filter(sender=sender)

        message_type = self.request.query_params.get('message_type', None)
        if message_type:
            queryset = queryset.filter(message_type=message_type)

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        is_system_message = self.request.query_params.get('is_system_message', None)
        if is_system_message is not None:
            is_system_message_bool = is_system_message.lower() == 'true'
            queryset = queryset.filter(is_system_message=is_system_message_bool)

        is_important = self.request.query_params.get('is_important', None)
        if is_important is not None:
            is_important_bool = is_important.lower() == 'true'
            queryset = queryset.filter(is_important=is_important_bool)

        # Apply search if provided
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(subject__icontains=search) |
                Q(content__icontains=search)
            )

        # Apply ordering if provided
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if ordering in ['sent_at', 'delivered_at', 'read_at',
                            '-sent_at', '-delivered_at', '-read_at']:
                queryset = queryset.order_by(ordering)

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
        """Create a new message"""
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            thread = serializer.validated_data.get('thread')
            user = request.user

            # Check if thread is closed
            if thread.status != 'active':
                return Response(
                    {"error": f"Cannot post messages to a {thread.get_status_display()} thread"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if user is active participant in thread
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

            # Set sender to current user
            message = serializer.save(sender=user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting a message.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAuthenticated],
        'patch': [permissions.IsAuthenticated],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get message by primary key"""
        message = get_object_or_404(Message, pk=pk)
        self.check_object_permissions(self.request, message)

        # Additional permission check for update actions
        if self.request.method in ['PUT', 'PATCH']:
            user = self.request.user
            if (user != message.sender and
                user != message.thread.creator and
                not user.is_staff):
                from rest_framework.exceptions import PermissionDenied
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
    """
    API view for marking a message as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, format=None):
        """Mark a message as read"""
        message = get_object_or_404(Message, pk=pk)
        user = request.user

        # Verify user is a participant in the thread
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

        # Avoid marking sender's own messages
        if message.sender == user:
            return Response(
                {'status': 'No need to mark your own messages as read'},
                status=status.HTTP_200_OK
            )

        # Mark as read using model method
        success = message.mark_as_read(reader=user)

        if success:
            return Response({'status': 'message marked as read'}, status=status.HTTP_200_OK)
        return Response(
            {'error': 'Failed to mark message as read'},
            status=status.HTTP_400_BAD_REQUEST
        )


class MyMessagesView(BaseAPIView):
    """
    API view for getting messages sent by the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get messages sent by the current user"""
        user = request.user
        messages = Message.objects.filter(sender=user)

        # Filter by thread if specified
        thread_id = request.query_params.get('thread_id', None)
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
    """
    API view for uploading attachment to a message.
    """
    model_class = Message
    file_field_name = 'attachments'
    allow_multiple = True
    max_file_size = 10 * 1024 * 1024  # 10MB

    def get_object(self, pk):
        """Get message by primary key with additional permissions check"""
        message = get_object_or_404(Message, pk=pk)

        # Only the sender can upload attachments to their own message
        user = self.request.user
        if user != message.sender and not user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only upload attachments to your own messages")

        # Check if the thread is active
        if message.thread.status != 'active':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Cannot upload attachments to messages in closed threads")

        return message



# TRANSACTION VIEWS
class TransactionListCreateView(BaseAPIView):
    """
    API view for listing and creating transactions.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [IsAgentPermission | permissions.IsAdminUser],
    }

    def get_queryset(self):
        """
        Customize queryset based on user role and request parameters.
        """
        queryset = Transaction.objects.all()
        user = self.request.user

        # Non-staff/non-agent users can only see transactions they're involved in
        if not user.is_staff and not user.has_role(Role.AGENT):
            queryset = queryset.filter(
                models.Q(from_user=user) |
                models.Q(to_user=user)
            )

        # Apply filtering
        transaction_type = self.request.query_params.get('transaction_type', None)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        from_user = self.request.query_params.get('from_user', None)
        if from_user:
            queryset = queryset.filter(from_user=from_user)

        to_user = self.request.query_params.get('to_user', None)
        if to_user:
            queryset = queryset.filter(to_user=to_user)

        payment = self.request.query_params.get('payment', None)
        if payment:
            queryset = queryset.filter(payment=payment)

        auction = self.request.query_params.get('auction', None)
        if auction:
            queryset = queryset.filter(auction=auction)

        contract = self.request.query_params.get('contract', None)
        if contract:
            queryset = queryset.filter(contract=contract)

        # Apply search if provided
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(transaction_number__icontains=search) |
                Q(description__icontains=search) |
                Q(reference__icontains=search)
            )

        # Apply ordering if provided
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            if ordering in ['transaction_date', 'amount', 'created_at',
                            '-transaction_date', '-amount', '-created_at']:
                queryset = queryset.order_by(ordering)

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
        """Create a new transaction"""
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting a transaction.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAdminUser],
        'patch': [permissions.IsAdminUser],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get transaction by primary key"""
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
    """
    API view for marking a transaction as completed.
    """
    permission_classes = [IsAgentPermission | permissions.IsAdminUser]

    def post(self, request, pk, format=None):
        """Mark transaction as completed"""
        transaction = get_object_or_404(Transaction, pk=pk)

        # Mark as completed
        success = transaction.mark_as_completed(processor=request.user)

        if success:
            return Response({'status': 'transaction marked as completed'}, status=status.HTTP_200_OK)
        return Response(
            {'error': 'Failed to mark transaction as completed'},
            status=status.HTTP_400_BAD_REQUEST
        )


class MarkTransactionAsFailedView(BaseAPIView):
    """
    API view for marking a transaction as failed.
    """
    permission_classes = [IsAgentPermission | permissions.IsAdminUser]

    def post(self, request, pk, format=None):
        """Mark transaction as failed"""
        transaction = get_object_or_404(Transaction, pk=pk)
        reason = request.data.get('reason', None)

        # Mark as failed
        success = transaction.mark_as_failed(reason=reason)

        if success:
            return Response({'status': 'transaction marked as failed'}, status=status.HTTP_200_OK)
        return Response(
            {'error': 'Failed to mark transaction as failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


class MyTransactionsView(BaseAPIView):
    """
    API view for getting transactions the current user is involved in.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get transactions the current user is involved in"""
        user = request.user
        transactions = Transaction.objects.filter(
            models.Q(from_user=user) |
            models.Q(to_user=user)
        )

        # Filter by type
        transaction_type = request.query_params.get('transaction_type', None)
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)

        # Filter by direction (incoming/outgoing)
        direction = request.query_params.get('direction', None)
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



class NotificationDetailView(BaseAPIView):
    """
    API view for retrieving, updating, and deleting a notification.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'put': [permissions.IsAdminUser],
        'patch': [permissions.IsAdminUser],
        'delete': [permissions.IsAdminUser],
    }

    def get_object(self, pk):
        """Get notification by primary key"""
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

class NotificationListCreateView(BaseAPIView):
    """
    API view for listing and creating notifications.
    """
    action_permission_map = {
        'get': [permissions.IsAuthenticated],
        'post': [permissions.IsAdminUser | IsAgentPermission],
    }

    def get_queryset(self):
        """Get filtered notification queryset."""
        queryset = Notification.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Non-staff users can only see their own notifications
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
        allowed_orderings = [
            'created_at', 'sent_at', 'read_at',
            '-created_at', '-sent_at', '-read_at'
        ]

        if ordering and ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)
        else:
            # Default ordering: newest first
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
        """Create a new notification"""
        serializer = NotificationSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                'validation_error',
                status.HTTP_400_BAD_REQUEST
            )

        try:
            notification = serializer.save()
            return self.success_response(
                data=serializer.data,
                message='Notification created successfully',
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return self.error_response(
                'Failed to create notification',
                'creation_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MarkNotificationAsReadView(BaseAPIView):
    """
    API view for marking a notification as read.
    """
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
                return self.success_response(
                    message='Notification already marked as read'
                )

            # Mark as read
            success = notification.mark_as_read()

            if success:
                return self.success_response(
                    message='Notification marked as read'
                )

            return self.error_response(
                'Failed to mark notification as read',
                'marking_failed',
                status.HTTP_400_BAD_REQUEST
            )

        except Http404:
            return self.not_found('Notification not found')
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return self.error_response(
                'An error occurred while marking the notification',
                'marking_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MarkAllNotificationsAsReadView(BaseAPIView):
    """
    API view for marking all notifications as read for the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, format=None):
        """Mark all notifications as read for the current user"""
        try:
            user = request.user
            count = Notification.objects.filter(
                recipient=user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )

            return self.success_response(
                message=f'{count} notifications marked as read'
            )
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return self.error_response(
                'Failed to mark notifications as read',
                'bulk_marking_error',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MyNotificationsView(BaseAPIView):
    """
    API view for getting notifications for the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get notifications for the current user"""
        user = request.user
        notifications = Notification.objects.filter(recipient=user)

        # Filter by read status
        read_status = request.query_params.get('is_read', None)
        if read_status is not None:
            is_read = read_status.lower() == 'true'
            notifications = notifications.filter(is_read=is_read)

        # Filter by type
        notification_type = request.query_params.get('notification_type', None)
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)

        # Handle pagination
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
