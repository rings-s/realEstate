from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils import timezone
from django.db.models import Q, Count, Sum, F, Value, CharField
from django.db.models.functions import Concat
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from .models import Document, Contract, Payment, Transaction, Property, Auction, Bid, PropertyView, MessageThread, Message, ThreadParticipant, Notification
from .serializers import (
    AuctionSerializer, AuctionDetailSerializer, AuctionListSerializer,
    DocumentSerializer, DocumentDetailSerializer, DocumentListSerializer,
    ContractSerializer, ContractDetailSerializer, ContractListSerializer,
    PaymentSerializer, PaymentDetailSerializer, PaymentListSerializer,
    TransactionSerializer, TransactionDetailSerializer,TransactionListSerializer,
    PropertyViewSerializer, PropertyViewDetailSerializer, PropertyViewListSerializer,
    MessageThreadSerializer, MessageThreadDetailSerializer, MessageThreadListSerializer,
    MessageSerializer, MessageDetailSerializer, MessageListSerializer,
    ThreadParticipantSerializer, ThreadParticipantDetailSerializer,
    NotificationSerializer, NotificationDetailSerializer, NotificationListSerializer, PropertySerializer, PropertyDetailSerializer, PropertyListSerializer,
    AuctionSerializer, AuctionDetailSerializer, AuctionListSerializer,
    BidSerializer, BidDetailSerializer, BidListSerializer
)
from accounts.models import CustomUser, Role

import logging
logger = logging.getLogger(__name__)


# ============== PROPERTY VIEWS ==============

@api_view(['GET'])
@permission_classes([AllowAny])
def property_list(request):
    """
    List all properties with filtering options.
    
    Query parameters:
    - property_type: Filter by property type
    - city: Filter by city
    - min_price: Filter by minimum price
    - max_price: Filter by maximum price
    - min_area: Filter by minimum area
    - max_area: Filter by maximum area
    - bedrooms: Filter by number of bedrooms
    - bathrooms: Filter by number of bathrooms
    - is_featured: Filter featured properties (true/false)
    - sort_by: Sort by field (created_at, price, area, etc.)
    - sort_order: asc or desc
    - search: Search in title, description, address
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        property_type = request.query_params.get('property_type')
        city = request.query_params.get('city')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        min_area = request.query_params.get('min_area')
        max_area = request.query_params.get('max_area')
        bedrooms = request.query_params.get('bedrooms')
        bathrooms = request.query_params.get('bathrooms')
        is_featured = request.query_params.get('is_featured')
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        search = request.query_params.get('search')
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        
        # Build query
        queryset = Property.objects.filter(is_published=True)
        
        # Apply filters
        if property_type:
            queryset = queryset.filter(property_type=property_type)
        
        if city:
            queryset = queryset.filter(city__iexact=city)
        
        if min_price:
            queryset = queryset.filter(estimated_value__gte=float(min_price))
        
        if max_price:
            queryset = queryset.filter(estimated_value__lte=float(max_price))
        
        if min_area:
            queryset = queryset.filter(area__gte=float(min_area))
        
        if max_area:
            queryset = queryset.filter(area__lte=float(max_area))
        
        if bedrooms:
            queryset = queryset.filter(bedrooms=int(bedrooms))
        
        if bathrooms:
            queryset = queryset.filter(bathrooms=int(bathrooms))
        
        if is_featured:
            is_featured_bool = is_featured.lower() == 'true'
            queryset = queryset.filter(is_featured=is_featured_bool)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) | 
                Q(address__icontains=search) |
                Q(city__icontains=search) |
                Q(district__icontains=search)
            )
        
        # Apply sorting
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['created_at', 'estimated_value', 'area', 'views_count', 'bedrooms', 'bathrooms']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = PropertyListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in property_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching properties.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def property_create(request):
    """
    Create a new property.
    Requires authentication and proper permissions.
    """
    try:
        # Check if user has seller role
        user = request.user
        if not user.has_role(Role.SELLER) and not user.is_staff:
            return Response(
                {"error": _("You don't have permission to create properties.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Initialize serializer with request data
        serializer = PropertySerializer(data=request.data)
        
        # Validate data
        if serializer.is_valid():
            # Set owner to current user if not provided
            if 'owner' not in serializer.validated_data:
                serializer.validated_data['owner'] = user
            
            # Save property
            property_obj = serializer.save()
            
            # Return success response
            return Response(
                PropertyDetailSerializer(property_obj).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in property_create: {str(e)}")
        return Response(
            {"error": _("An error occurred while creating the property.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def property_detail(request, pk=None, slug=None):
    """
    Retrieve property details by ID or slug.
    Increments the view count for the property.
    """
    try:
        # Get property by ID or slug
        if pk:
            property_obj = get_object_or_404(Property, pk=pk)
        elif slug:
            property_obj = get_object_or_404(Property, slug=slug)
        else:
            return Response(
                {"error": _("Property ID or slug is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if property is published or user has access
        if not property_obj.is_published and request.user != property_obj.owner and not request.user.is_staff:
            return Response(
                {"error": _("This property is not available.")},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Increment view count
        property_obj.views_count += 1
        property_obj.save(update_fields=['views_count'])
        
        # Serialize and return data
        serializer = PropertyDetailSerializer(property_obj)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in property_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the property details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def property_update(request, pk):
    """
    Update a property (PUT for full update, PATCH for partial update).
    Requires authentication and proper ownership/permissions.
    """
    try:
        # Get property
        property_obj = get_object_or_404(Property, pk=pk)
        
        # Check permissions
        user = request.user
        if not (user == property_obj.owner or user.is_staff):
            return Response(
                {"error": _("You don't have permission to update this property.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Determine if this is a full or partial update
        partial = request.method == 'PATCH'
        
        # Initialize serializer with instance and data
        serializer = PropertySerializer(
            property_obj, 
            data=request.data, 
            partial=partial
        )
        
        # Validate data
        if serializer.is_valid():
            # Add validation for transitions here if needed
            property_obj = serializer.save(user=user)
            
            # Return updated data
            return Response(PropertyDetailSerializer(property_obj).data)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except ValidationError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in property_update: {str(e)}")
        return Response(
            {"error": _("An error occurred while updating the property.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def property_delete(request, pk):
    """
    Delete a property.
    Requires authentication and proper ownership/permissions.
    """
    try:
        # Get property
        property_obj = get_object_or_404(Property, pk=pk)
        
        # Check permissions
        user = request.user
        if not (user == property_obj.owner or user.is_staff):
            return Response(
                {"error": _("You don't have permission to delete this property.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if property has active auctions
        if property_obj.auctions.filter(status__in=['active', 'pending']).exists():
            return Response(
                {"error": _("Cannot delete property with active auctions.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete property
        property_obj.delete()
        
        # Return success response
        return Response(
            {"message": _("Property deleted successfully.")},
            status=status.HTTP_204_NO_CONTENT
        )
    
    except Exception as e:
        logger.error(f"Error in property_delete: {str(e)}")
        return Response(
            {"error": _("An error occurred while deleting the property.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_properties(request):
    """
    List all properties owned by the current user.
    """
    try:
        # Get properties for current user
        queryset = Property.objects.filter(owner=request.user)
        
        # Apply sorting
        queryset = queryset.order_by('-created_at')
        
        # Serialize data
        serializer = PropertyListSerializer(queryset, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in user_properties: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching your properties.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def recommended_properties(request, pk):
    """
    Get recommended properties similar to the specified property.
    """
    try:
        # Get property
        property_obj = get_object_or_404(Property, pk=pk)
        
        # Get recommended properties
        recommended = property_obj.recommended_properties(limit=5)
        
        # Serialize data
        serializer = PropertyListSerializer(recommended, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in recommended_properties: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching recommended properties.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== AUCTION VIEWS ==============

@api_view(['GET'])
@permission_classes([AllowAny])
def auction_list(request):
    """
    List all auctions with filtering options.
    
    Query parameters:
    - status: Filter by auction status
    - auction_type: Filter by auction type
    - min_price: Filter by minimum starting price
    - max_price: Filter by maximum starting price
    - property_type: Filter by property type
    - city: Filter by city
    - is_featured: Filter featured auctions (true/false)
    - is_active: Filter currently active auctions (true/false)
    - sort_by: Sort by field (created_at, start_date, end_date, etc.)
    - sort_order: asc or desc
    - search: Search in title, description
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        status = request.query_params.get('status')
        auction_type = request.query_params.get('auction_type')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        property_type = request.query_params.get('property_type')
        city = request.query_params.get('city')
        is_featured = request.query_params.get('is_featured')
        is_active = request.query_params.get('is_active')
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        search = request.query_params.get('search')
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        
        # Build base query for published auctions
        queryset = Auction.objects.filter(is_published=True)
        
        # Apply filters
        if status:
            queryset = queryset.filter(status=status)
        
        if auction_type:
            queryset = queryset.filter(auction_type=auction_type)
        
        if min_price:
            queryset = queryset.filter(starting_price__gte=float(min_price))
        
        if max_price:
            queryset = queryset.filter(starting_price__lte=float(max_price))
        
        if property_type:
            queryset = queryset.filter(related_property__property_type=property_type)
        
        if city:
            queryset = queryset.filter(related_property__city__iexact=city)
        
        if is_featured:
            is_featured_bool = is_featured.lower() == 'true'
            queryset = queryset.filter(is_featured=is_featured_bool)
        
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            now = timezone.now()
            if is_active_bool:
                queryset = queryset.filter(
                    status='active',
                    start_date__lte=now,
                    end_date__gte=now
                )
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(related_property__title__icontains=search) |
                Q(related_property__city__icontains=search)
            )
        
        # Apply sorting
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['created_at', 'start_date', 'end_date', 'starting_price', 'views_count']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = AuctionListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in auction_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching auctions.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auction_create(request):
    """
    Create a new auction.
    Requires authentication and proper permissions.
    """
    try:
        # Check if user has auctioneer role
        user = request.user
        if not (user.has_role(Role.SELLER) or user.is_staff):
            return Response(
                {"error": _("You don't have permission to create auctions.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Initialize serializer with request data
        serializer = AuctionSerializer(data=request.data)
        
        # Validate data
        if serializer.is_valid():
            # Check if user owns the property or is staff
            property_id = serializer.validated_data.get('related_property').id
            property_obj = get_object_or_404(Property, pk=property_id)
            
            if not (property_obj.owner == user or user.is_staff):
                return Response(
                    {"error": _("You can only create auctions for properties you own.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Set created_by to current user
            serializer.validated_data['created_by'] = user
            
            # Set auctioneer to current user if not provided
            if 'auctioneer' not in serializer.validated_data:
                serializer.validated_data['auctioneer'] = user
            
            # Save auction
            auction_obj = serializer.save()
            
            # Return success response
            return Response(
                AuctionDetailSerializer(auction_obj).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in auction_create: {str(e)}")
        return Response(
            {"error": _("An error occurred while creating the auction.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def auction_detail(request, pk=None, slug=None):
    """
    Retrieve auction details by ID or slug.
    Increments the view count for the auction.
    """
    try:
        # Get auction by ID or slug
        if pk:
            auction_obj = get_object_or_404(Auction, pk=pk)
        elif slug:
            auction_obj = get_object_or_404(Auction, slug=slug)
        else:
            return Response(
                {"error": _("Auction ID or slug is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if auction is published or user has access
        if not auction_obj.is_published:
            user = request.user
            # Check if user is authenticated and has access
            if not user.is_authenticated or (
                user != auction_obj.created_by and 
                user != auction_obj.auctioneer and 
                user != auction_obj.related_property.owner and
                not user.is_staff
            ):
                return Response(
                    {"error": _("This auction is not available.")},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # If auction is private, check if user is invited
        if auction_obj.is_private and request.user.is_authenticated:
            if not (
                request.user.is_staff or 
                request.user == auction_obj.created_by or
                request.user == auction_obj.auctioneer or
                auction_obj.invited_bidders.filter(id=request.user.id).exists()
            ):
                return Response(
                    {"error": _("This is a private auction. You must be invited to view it.")},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Increment view count
        auction_obj.views_count += 1
        auction_obj.save(update_fields=['views_count'])
        
        # Get bids data for the auction
        bids = auction_obj.bids.all().order_by('-bid_amount')[:10]
        bids_serializer = BidListSerializer(bids, many=True)
        
        # Serialize auction data
        auction_serializer = AuctionDetailSerializer(auction_obj)
        
        # Combine data for response
        response_data = auction_serializer.data
        response_data['recent_bids'] = bids_serializer.data
        
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"Error in auction_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the auction details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def auction_update(request, pk):
    """
    Update an auction (PUT for full update, PATCH for partial update).
    Requires authentication and proper ownership/permissions.
    """
    try:
        # Get auction
        auction_obj = get_object_or_404(Auction, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user == auction_obj.created_by or 
            user == auction_obj.auctioneer or 
            user.is_staff
        ):
            return Response(
                {"error": _("You don't have permission to update this auction.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if auction can be modified (not active or closed)
        if auction_obj.status in ['closed', 'sold', 'cancelled']:
            return Response(
                {"error": _("This auction cannot be modified in its current state.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine if this is a full or partial update
        partial = request.method == 'PATCH'
        
        # Initialize serializer with instance and data
        serializer = AuctionSerializer(
            auction_obj, 
            data=request.data, 
            partial=partial
        )
        
        # Validate data
        if serializer.is_valid():
            # Save auction
            auction_obj = serializer.save()
            
            # Return updated data
            return Response(AuctionDetailSerializer(auction_obj).data)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except ValidationError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in auction_update: {str(e)}")
        return Response(
            {"error": _("An error occurred while updating the auction.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def auction_delete(request, pk):
    """
    Delete an auction.
    Requires authentication and proper ownership/permissions.
    """
    try:
        # Get auction
        auction_obj = get_object_or_404(Auction, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user == auction_obj.created_by or 
            user.is_staff
        ):
            return Response(
                {"error": _("You don't have permission to delete this auction.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if auction can be deleted (must be draft or cancelled)
        if auction_obj.status not in ['draft', 'cancelled']:
            return Response(
                {"error": _("Only draft or cancelled auctions can be deleted.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete auction
        auction_obj.delete()
        
        # Return success response
        return Response(
            {"message": _("Auction deleted successfully.")},
            status=status.HTTP_204_NO_CONTENT
        )
    
    except Exception as e:
        logger.error(f"Error in auction_delete: {str(e)}")
        return Response(
            {"error": _("An error occurred while deleting the auction.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_auctions(request):
    """
    List all auctions created by the current user.
    """
    try:
        # Get auctions for current user
        queryset = Auction.objects.filter(created_by=request.user)
        
        # Apply sorting
        queryset = queryset.order_by('-created_at')
        
        # Serialize data
        serializer = AuctionListSerializer(queryset, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in user_auctions: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching your auctions.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auction_extend(request, pk):
    """
    Extend an auction's end time.
    Requires authentication and proper ownership/permissions.
    """
    try:
        # Get auction
        auction_obj = get_object_or_404(Auction, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user == auction_obj.created_by or 
            user == auction_obj.auctioneer or 
            user.is_staff
        ):
            return Response(
                {"error": _("You don't have permission to extend this auction.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate auction status
        if auction_obj.status != 'active':
            return Response(
                {"error": _("Only active auctions can be extended.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get extension minutes from request or use default
        minutes = request.data.get('minutes', auction_obj.extension_minutes)
        
        try:
            minutes = int(minutes)
            if minutes <= 0:
                raise ValueError("Extension minutes must be positive")
        except (TypeError, ValueError):
            return Response(
                {"error": _("Invalid extension minutes.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extend auction
        original_end_date = auction_obj.end_date
        auction_obj.extend_auction(minutes=minutes)
        
        # Return success response
        return Response({
            "message": _("Auction extended successfully."),
            "original_end_date": original_end_date,
            "new_end_date": auction_obj.end_date,
            "extension_minutes": minutes
        })
    
    except ValidationError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in auction_extend: {str(e)}")
        return Response(
            {"error": _("An error occurred while extending the auction.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auction_invite(request, pk):
    """
    Invite users to a private auction.
    Requires authentication and proper ownership/permissions.
    """
    try:
        # Get auction
        auction_obj = get_object_or_404(Auction, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user == auction_obj.created_by or 
            user == auction_obj.auctioneer or 
            user.is_staff
        ):
            return Response(
                {"error": _("You don't have permission to invite users to this auction.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate auction is private
        if not auction_obj.is_private:
            return Response(
                {"error": _("Only private auctions support invitations.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user IDs or emails from request
        user_ids = request.data.get('user_ids', [])
        emails = request.data.get('emails', [])
        
        if not user_ids and not emails:
            return Response(
                {"error": _("Please provide user_ids or emails to invite.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Invite users by ID
        invited_users = []
        for user_id in user_ids:
            try:
                invite_user = CustomUser.objects.get(id=user_id)
                auction_obj.invited_bidders.add(invite_user)
                invited_users.append(invite_user.email)
            except CustomUser.DoesNotExist:
                continue
        
        # Invite users by email
        for email in emails:
            try:
                invite_user = CustomUser.objects.get(email=email)
                auction_obj.invited_bidders.add(invite_user)
                invited_users.append(email)
            except CustomUser.DoesNotExist:
                continue
        
        # Return success response
        return Response({
            "message": _("Users invited successfully."),
            "invited_users": invited_users
        })
    
    except Exception as e:
        logger.error(f"Error in auction_invite: {str(e)}")
        return Response(
            {"error": _("An error occurred while inviting users.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== BID VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bid_list(request, auction_pk=None):
    """
    List bids for an auction or all bids made by current user.
    
    Query parameters:
    - auction_id: Filter by auction ID (if not provided in URL)
    - status: Filter by bid status
    - min_amount: Filter by minimum bid amount
    - max_amount: Filter by maximum bid amount
    - sort_by: Sort by field (bid_time, bid_amount, etc.)
    - sort_order: asc or desc
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Build base query
        queryset = Bid.objects.all()
        
        # Filter by auction if provided
        if auction_pk:
            auction_obj = get_object_or_404(Auction, pk=auction_pk)
            queryset = queryset.filter(auction=auction_obj)
            
            # Check if user has permission to view bids for this auction
            user = request.user
            if not (
                user == auction_obj.created_by or 
                user == auction_obj.auctioneer or 
                user.is_staff
            ):
                # Only show user's own bids if not auction owner/auctioneer/staff
                queryset = queryset.filter(bidder=user)
        else:
            # Get query parameters
            auction_id = request.query_params.get('auction_id')
            
            # If no auction_pk in URL but auction_id in query params, filter by it
            if auction_id:
                auction_obj = get_object_or_404(Auction, pk=auction_id)
                queryset = queryset.filter(auction=auction_obj)
                
                # Check permissions as above
                user = request.user
                if not (
                    user == auction_obj.created_by or 
                    user == auction_obj.auctioneer or 
                    user.is_staff
                ):
                    queryset = queryset.filter(bidder=user)
            else:
                # If no auction specified, only show user's own bids
                queryset = queryset.filter(bidder=request.user)
        
        # Apply additional filters
        status = request.query_params.get('status')
        min_amount = request.query_params.get('min_amount')
        max_amount = request.query_params.get('max_amount')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if min_amount:
            queryset = queryset.filter(bid_amount__gte=float(min_amount))
        
        if max_amount:
            queryset = queryset.filter(bid_amount__lte=float(max_amount))
        
        # Apply sorting
        sort_by = request.query_params.get('sort_by', 'bid_time')
        sort_order = request.query_params.get('sort_order', 'desc')
        
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['bid_time', 'bid_amount', 'created_at']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        
        # Apply pagination
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        total_count = queryset.count()
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = BidListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in bid_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching bids.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_bid(request, auction_pk):
    """
    Place a bid on an auction.
    Requires authentication and proper permissions.
    """
    try:
        # Get auction
        auction_obj = get_object_or_404(Auction, pk=auction_pk)
        
        # Validate auction status
        if auction_obj.status != 'active':
            return Response(
                {"error": _("Bids can only be placed on active auctions.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate auction timing
        now = timezone.now()
        if now < auction_obj.start_date:
            return Response(
                {"error": _("The auction hasn't started yet.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if now > auction_obj.end_date:
            return Response(
                {"error": _("The auction has already ended.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if private auction and user is invited
        user = request.user
        if auction_obj.is_private:
            if not auction_obj.invited_bidders.filter(id=user.id).exists():
                return Response(
                    {"error": _("This is a private auction. You must be invited to place a bid.")},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Check if user has buyer role
        if not user.has_role(Role.BUYER) and not user.is_staff:
            return Response(
                {"error": _("You don't have permission to place bids.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get bid amount from request
        bid_amount = request.data.get('bid_amount')
        if not bid_amount:
            return Response(
                {"error": _("Bid amount is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            bid_amount = float(bid_amount)
        except (TypeError, ValueError):
            return Response(
                {"error": _("Invalid bid amount.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get highest current bid
        highest_bid = auction_obj.highest_bid
        min_bid = highest_bid + auction_obj.min_bid_increment
        
        # Validate bid amount
        if bid_amount < min_bid:
            return Response(
                {"error": _("Bid must be at least {0}.").format(min_bid)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create bid
        bid = Bid.objects.create(
            auction=auction_obj,
            bidder=user,
            bid_amount=bid_amount,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # For auto bidding if implemented
        max_bid_amount = request.data.get('max_bid_amount')
        if max_bid_amount:
            try:
                max_bid_amount = float(max_bid_amount)
                if max_bid_amount > bid_amount:
                    bid.max_bid_amount = max_bid_amount
                    bid.is_auto_bid = True
                    bid.save(update_fields=['max_bid_amount', 'is_auto_bid'])
            except (TypeError, ValueError):
                pass  # Ignore invalid max_bid_amount
        
        # Create notification for auction owner
        if auction_obj.created_by != user:
            Notification.create_bid_notification(bid, recipient=auction_obj.created_by)
        
        # Create notification for property owner if different
        property_owner = auction_obj.related_property.owner
        if property_owner != auction_obj.created_by and property_owner != user:
            Notification.create_bid_notification(bid, recipient=property_owner)
        
        # Return success response
        serializer = BidDetailSerializer(bid)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    except ValidationError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in place_bid: {str(e)}")
        return Response(
            {"error": _("An error occurred while placing your bid.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bid_detail(request, pk):
    """
    Retrieve bid details.
    Requires authentication and proper ownership/permissions.
    """
    try:
        # Get bid
        bid_obj = get_object_or_404(Bid, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user == bid_obj.bidder or 
            user == bid_obj.auction.created_by or 
            user == bid_obj.auction.auctioneer or 
            user.is_staff
        ):
            return Response(
                {"error": _("You don't have permission to view this bid.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and return data
        serializer = BidDetailSerializer(bid_obj)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in bid_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the bid details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_winning_bid(request, pk):
    """
    Mark a bid as the winning bid for an auction.
    Requires authentication and proper permissions.
    """
    try:
        # Get bid
        bid_obj = get_object_or_404(Bid, pk=pk)
        auction_obj = bid_obj.auction
        
        # Check permissions
        user = request.user
        if not (
            user == auction_obj.created_by or 
            user == auction_obj.auctioneer or 
            user.is_staff
        ):
            return Response(
                {"error": _("You don't have permission to mark winning bids.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate auction status
        if auction_obj.status not in ['active', 'extended', 'closed']:
            return Response(
                {"error": _("Can only mark winning bid for active, extended, or closed auctions.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark bid as winning
        result = bid_obj.mark_as_winning()
        
        if not result:
            return Response(
                {"error": _("Failed to mark bid as winning.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update auction status if needed
        if auction_obj.status != 'closed':
            auction_obj.status = 'closed'
            auction_obj.save(update_fields=['status'])
        
        # Create notification for winning bidder
        Notification.objects.create(
            recipient=bid_obj.bidder,
            notification_type='winning_bid',
            title=_("Congratulations! Your bid won"),
            content=_("Your bid of {0} on {1} has been selected as the winning bid.").format(
                bid_obj.bid_amount, auction_obj.title
            ),
            related_auction=auction_obj,
            related_bid=bid_obj,
            related_property=auction_obj.related_property,
            icon='trophy',
            color='success',
            action_url=f'/auctions/{auction_obj.id}'
        )
        
        # Return success response
        return Response({
            "message": _("Bid marked as winning successfully."),
            "auction_status": auction_obj.status,
            "winning_bid": bid_obj.bid_amount,
            "winning_bidder": bid_obj.bidder.get_full_name() or bid_obj.bidder.email
        })
    
    except Exception as e:
        logger.error(f"Error in mark_winning_bid: {str(e)}")
        return Response(
            {"error": _("An error occurred while marking the winning bid.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bids(request):
    """
    List all bids made by the current user.
    """
    try:
        # Get bids for current user
        queryset = Bid.objects.filter(bidder=request.user)
        
        # Apply sorting
        queryset = queryset.order_by('-bid_time')
        
        # Serialize data
        serializer = BidListSerializer(queryset, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in user_bids: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching your bids.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auction_stats(request, pk):
    """
    Get statistics for an auction.
    """
    try:
        # Get auction
        auction_obj = get_object_or_404(Auction, pk=pk)
        
        # Gather statistics
        total_bids = auction_obj.bids.count()
        unique_bidders = auction_obj.bids.values('bidder').distinct().count()
        highest_bid = auction_obj.highest_bid
        
        # Calculate average bid amount
        avg_bid = auction_obj.bids.aggregate(Avg('bid_amount'))['bid_amount__avg'] or 0
        
        # Count bids by hour (last 24 hours)
        now = timezone.now()
        last_day = now - timedelta(days=1)
        bids_last_day = auction_obj.bids.filter(bid_time__gte=last_day).count()
        
        # Time remaining
        time_remaining = auction_obj.time_remaining
        
        # Return statistics
        return Response({
            "total_bids": total_bids,
            "unique_bidders": unique_bidders,
            "highest_bid": highest_bid,
            "average_bid": avg_bid,
            "bids_last_24h": bids_last_day,
            "time_remaining_seconds": time_remaining,
            "is_active": auction_obj.is_active
        })
    
    except Exception as e:
        logger.error(f"Error in auction_stats: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching auction statistics.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




# ============== DOCUMENT VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_list(request):
    """
    List documents with filtering options.
    
    Query parameters:
    - document_type: Filter by document type
    - property_id: Filter by related property
    - auction_id: Filter by related auction
    - contract_id: Filter by related contract
    - verification_status: Filter by verification status
    - sort_by: Sort by field (created_at, document_type, etc.)
    - sort_order: asc or desc
    - search: Search in title, description
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        document_type = request.query_params.get('document_type')
        property_id = request.query_params.get('property_id')
        auction_id = request.query_params.get('auction_id')
        contract_id = request.query_params.get('contract_id')
        verification_status = request.query_params.get('verification_status')
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        search = request.query_params.get('search')
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        
        # Base query - filter by user access
        user = request.user
        
        if user.is_staff:
            # Staff can see all documents
            queryset = Document.objects.all()
        else:
            # Regular users can only see documents they uploaded or have access to
            queryset = Document.objects.filter(
                Q(uploaded_by=user) |
                Q(related_property__owner=user) |
                Q(auction__created_by=user) |
                Q(auction__auctioneer=user) |
                Q(contract__buyer=user) |
                Q(contract__seller=user) |
                Q(contract__agent=user)
            ).distinct()
        
        # Apply filters
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        if property_id:
            queryset = queryset.filter(related_property_id=property_id)
        
        if auction_id:
            queryset = queryset.filter(auction_id=auction_id)
        
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(document_number__icontains=search)
            )
        
        # Apply sorting
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['created_at', 'document_type', 'verification_status', 'issue_date', 'expiry_date']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = DocumentListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in document_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching documents.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_create(request):
    """
    Create a new document.
    Requires authentication.
    """
    try:
        # Initialize serializer with request data
        serializer = DocumentSerializer(data=request.data)
        
        # Validate data
        if serializer.is_valid():
            # Set uploaded_by to current user if not provided
            if 'uploaded_by' not in serializer.validated_data:
                serializer.validated_data['uploaded_by'] = request.user
            
            # Validate user has access to the related entity
            user = request.user
            
            related_property = serializer.validated_data.get('related_property')
            if related_property and not (user.is_staff or related_property.owner == user):
                return Response(
                    {"error": _("You don't have permission to upload documents for this property.")},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            auction = serializer.validated_data.get('auction')
            if auction and not (user.is_staff or auction.created_by == user or auction.auctioneer == user):
                return Response(
                    {"error": _("You don't have permission to upload documents for this auction.")},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            contract = serializer.validated_data.get('contract')
            if contract and not (
                user.is_staff or 
                contract.buyer == user or 
                contract.seller == user or 
                contract.agent == user
            ):
                return Response(
                    {"error": _("You don't have permission to upload documents for this contract.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Save document
            document = serializer.save()
            
            # Return success response
            return Response(
                DocumentDetailSerializer(document).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in document_create: {str(e)}")
        return Response(
            {"error": _("An error occurred while creating the document.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_detail(request, pk):
    """
    Retrieve document details.
    Requires authentication and proper access permissions.
    """
    try:
        # Get document
        document = get_object_or_404(Document, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user.is_staff or
            document.uploaded_by == user or
            (document.related_property and document.related_property.owner == user) or
            (document.auction and (document.auction.created_by == user or document.auction.auctioneer == user)) or
            (document.contract and (
                document.contract.buyer == user or 
                document.contract.seller == user or 
                document.contract.agent == user
            ))
        ):
            return Response(
                {"error": _("You don't have permission to view this document.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and return data
        serializer = DocumentDetailSerializer(document)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in document_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the document details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def document_update(request, pk):
    """
    Update a document (PUT for full update, PATCH for partial update).
    Requires authentication and proper access permissions.
    """
    try:
        # Get document
        document = get_object_or_404(Document, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user.is_staff or
            document.uploaded_by == user or
            (document.related_property and document.related_property.owner == user)
        ):
            return Response(
                {"error": _("You don't have permission to update this document.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Staff can update verification status, others cannot
        if not user.is_staff and 'verification_status' in request.data:
            return Response(
                {"error": _("Only staff can update verification status.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Determine if this is a full or partial update
        partial = request.method == 'PATCH'
        
        # Initialize serializer with instance and data
        serializer = DocumentSerializer(
            document, 
            data=request.data, 
            partial=partial
        )
        
        # Validate data
        if serializer.is_valid():
            # Save document
            document = serializer.save()
            
            # Return updated data
            return Response(DocumentDetailSerializer(document).data)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except ValidationError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in document_update: {str(e)}")
        return Response(
            {"error": _("An error occurred while updating the document.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def document_delete(request, pk):
    """
    Delete a document.
    Requires authentication and proper access permissions.
    """
    try:
        # Get document
        document = get_object_or_404(Document, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user.is_staff or
            document.uploaded_by == user or
            (document.related_property and document.related_property.owner == user)
        ):
            return Response(
                {"error": _("You don't have permission to delete this document.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Don't allow deleting verified documents
        if document.verification_status == 'verified' and not user.is_staff:
            return Response(
                {"error": _("Verified documents cannot be deleted.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete document
        document.delete()
        
        # Return success response
        return Response(
            {"message": _("Document deleted successfully.")},
            status=status.HTTP_204_NO_CONTENT
        )
    
    except Exception as e:
        logger.error(f"Error in document_delete: {str(e)}")
        return Response(
            {"error": _("An error occurred while deleting the document.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_documents(request):
    """
    List all documents uploaded by the current user.
    """
    try:
        # Get documents for current user
        queryset = Document.objects.filter(uploaded_by=request.user)
        
        # Apply sorting
        queryset = queryset.order_by('-created_at')
        
        # Serialize data
        serializer = DocumentListSerializer(queryset, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in user_documents: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching your documents.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_document(request, pk):
    """
    Verify a document.
    Requires staff permissions.
    """
    try:
        # Check staff permissions
        if not request.user.is_staff:
            return Response(
                {"error": _("Only staff can verify documents.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get document
        document = get_object_or_404(Document, pk=pk)
        
        # Get verification notes from request
        notes = request.data.get('notes')
        
        # Verify document
        result = document.verify(request.user, notes)
        
        if not result:
            return Response(
                {"error": _("Failed to verify document.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response
        return Response({
            "message": _("Document verified successfully."),
            "verification_status": document.verification_status,
            "verified_by": request.user.get_full_name() or request.user.email,
            "verification_date": document.verification_date
        })
    
    except Exception as e:
        logger.error(f"Error in verify_document: {str(e)}")
        return Response(
            {"error": _("An error occurred while verifying the document.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== CONTRACT VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contract_list(request):
    """
    List contracts with filtering options.
    
    Query parameters:
    - property_id: Filter by related property
    - auction_id: Filter by related auction
    - status: Filter by contract status
    - buyer_id: Filter by buyer
    - seller_id: Filter by seller
    - sort_by: Sort by field (created_at, contract_date, etc.)
    - sort_order: asc or desc
    - search: Search in title, description
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        property_id = request.query_params.get('property_id')
        auction_id = request.query_params.get('auction_id')
        status = request.query_params.get('status')
        buyer_id = request.query_params.get('buyer_id')
        seller_id = request.query_params.get('seller_id')
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        search = request.query_params.get('search')
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        
        # Base query - filter by user access
        user = request.user
        
        if user.is_staff:
            # Staff can see all contracts
            queryset = Contract.objects.all()
        else:
            # Regular users can only see contracts they're involved in
            queryset = Contract.objects.filter(
                Q(buyer=user) |
                Q(seller=user) |
                Q(agent=user)
            ).distinct()
        
        # Apply filters
        if property_id:
            queryset = queryset.filter(related_property_id=property_id)
        
        if auction_id:
            queryset = queryset.filter(auction_id=auction_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if buyer_id and user.is_staff:
            queryset = queryset.filter(buyer_id=buyer_id)
        
        if seller_id and user.is_staff:
            queryset = queryset.filter(seller_id=seller_id)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(contract_number__icontains=search) |
                Q(notes__icontains=search)
            )
        
        # Apply sorting
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['created_at', 'contract_date', 'effective_date', 'expiry_date', 'contract_amount']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = ContractListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in contract_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching contracts.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contract_create(request):
    """
    Create a new contract.
    Requires authentication and proper permissions.
    """
    try:
        # Check permissions
        user = request.user
        if not (user.is_staff or user.has_role(Role.SELLER)):
            return Response(
                {"error": _("You don't have permission to create contracts.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Initialize serializer with request data
        serializer = ContractSerializer(data=request.data)
        
        # Validate data
        if serializer.is_valid():
            # Validate auction ownership
            auction_id = serializer.validated_data.get('auction').id
            auction = get_object_or_404(Auction, pk=auction_id)
            
            if not (user.is_staff or auction.created_by == user or auction.auctioneer == user):
                return Response(
                    {"error": _("You can only create contracts for auctions you manage.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate property ownership matches auction property
            property_id = serializer.validated_data.get('related_property').id
            if auction.related_property.id != property_id:
                return Response(
                    {"error": _("The property must match the auction's property.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate buyer matches winning bidder if auction has one
            buyer_id = serializer.validated_data.get('buyer').id
            if auction.winning_bidder and auction.winning_bidder.id != buyer_id:
                return Response(
                    {"error": _("The buyer should match the auction's winning bidder.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save contract
            contract = serializer.save()
            
            # Return success response
            return Response(
                ContractDetailSerializer(contract).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in contract_create: {str(e)}")
        return Response(
            {"error": _("An error occurred while creating the contract.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contract_detail(request, pk):
    """
    Retrieve contract details.
    Requires authentication and proper access permissions.
    """
    try:
        # Get contract
        contract = get_object_or_404(Contract, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user.is_staff or
            contract.buyer == user or
            contract.seller == user or
            contract.agent == user
        ):
            return Response(
                {"error": _("You don't have permission to view this contract.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and return data
        serializer = ContractDetailSerializer(contract)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in contract_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the contract details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def contract_update(request, pk):
    """
    Update a contract (PUT for full update, PATCH for partial update).
    Requires authentication and proper access permissions.
    """
    try:
        # Get contract
        contract = get_object_or_404(Contract, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user.is_staff or
            (contract.agent == user and contract.status in ['draft', 'pending_review'])
        ):
            return Response(
                {"error": _("You don't have permission to update this contract.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if contract can be modified
        if not user.is_staff and contract.status not in ['draft', 'pending_review', 'pending_buyer', 'pending_seller']:
            return Response(
                {"error": _("This contract cannot be modified in its current state.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine if this is a full or partial update
        partial = request.method == 'PATCH'
        
        # Initialize serializer with instance and data
        serializer = ContractSerializer(
            contract, 
            data=request.data, 
            partial=partial
        )
        
        # Validate data
        if serializer.is_valid():
            # Prevent changing key fields for non-staff users
            if not user.is_staff:
                disallowed_fields = ['buyer', 'seller', 'auction', 'related_property']
                for field in disallowed_fields:
                    if field in serializer.validated_data:
                        return Response(
                            {"error": _(f"Only staff can update {field}.")},
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            # Save contract
            contract = serializer.save()
            
            # Return updated data
            return Response(ContractDetailSerializer(contract).data)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except ValidationError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in contract_update: {str(e)}")
        return Response(
            {"error": _("An error occurred while updating the contract.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sign_contract(request, pk):
    """
    Sign a contract.
    Requires authentication as buyer or seller.
    """
    try:
        # Get contract
        contract = get_object_or_404(Contract, pk=pk)
        
        # Check permissions
        user = request.user
        role = request.data.get('role')
        
        if role not in ['buyer', 'seller', 'agent']:
            return Response(
                {"error": _("Invalid role. Must be 'buyer', 'seller', or 'agent'.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate user matches the role
        if role == 'buyer' and contract.buyer != user:
            return Response(
                {"error": _("You are not the buyer of this contract.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if role == 'seller' and contract.seller != user:
            return Response(
                {"error": _("You are not the seller of this contract.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if role == 'agent' and contract.agent != user:
            return Response(
                {"error": _("You are not the agent for this contract.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if contract can be signed
        if contract.status not in ['draft', 'pending_review', 'pending_buyer', 'pending_seller']:
            return Response(
                {"error": _("This contract cannot be signed in its current state.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sign contract based on role
        if role == 'buyer':
            if contract.buyer_signed:
                return Response(
                    {"error": _("You have already signed this contract.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            result = contract.sign_as_buyer(user)
        elif role == 'seller':
            if contract.seller_signed:
                return Response(
                    {"error": _("You have already signed this contract.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            result = contract.sign_as_seller(user)
        else:  # agent
            if contract.agent_signed:
                return Response(
                    {"error": _("You have already signed this contract.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            contract.agent_signed = True
            contract.agent_signature_date = timezone.now()
            contract.save(update_fields=['agent_signed', 'agent_signature_date', 'updated_at'])
            result = True
        
        if not result:
            return Response(
                {"error": _("Failed to sign contract.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response with updated contract
        serializer = ContractDetailSerializer(contract)
        return Response({
            "message": _("Contract signed successfully."),
            "contract": serializer.data
        })
    
    except ValidationError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in sign_contract: {str(e)}")
        return Response(
            {"error": _("An error occurred while signing the contract.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_contracts(request):
    """
    List all contracts associated with the current user.
    """
    try:
        # Get role parameter
        role = request.query_params.get('role')
        
        # Get contracts for current user
        user = request.user
        if role == 'buyer':
            queryset = Contract.objects.filter(buyer=user)
        elif role == 'seller':
            queryset = Contract.objects.filter(seller=user)
        elif role == 'agent':
            queryset = Contract.objects.filter(agent=user)
        else:
            # All contracts involving the user
            queryset = Contract.objects.filter(
                Q(buyer=user) | Q(seller=user) | Q(agent=user)
            ).distinct()
        
        # Apply sorting
        queryset = queryset.order_by('-created_at')
        
        # Serialize data
        serializer = ContractListSerializer(queryset, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in user_contracts: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching your contracts.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_contract_status(request, pk):
    """
    Update contract status.
    Requires authentication and proper access permissions.
    """
    try:
        # Get contract
        contract = get_object_or_404(Contract, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user.is_staff or
            (contract.agent == user and contract.status in ['signed', 'pending_payment'])
        ):
            return Response(
                {"error": _("You don't have permission to update this contract's status.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get new status from request
        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {"error": _("New status is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if status transition is valid
        old_status = contract.status
        
        # Manual validation for common transitions
        valid_transitions = {}
        
        if user.is_staff:
            # Staff can perform most transitions
            valid_transitions = Contract.STATUS_TRANSITIONS
        else:
            # Agent can only perform limited transitions
            valid_transitions = {
                'signed': ['pending_payment', 'active'],
                'pending_payment': ['active'],
                'active': ['completed']
            }
        
        if new_status not in valid_transitions.get(old_status, []):
            return Response(
                {"error": _(f"Invalid status transition from '{old_status}' to '{new_status}'.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status
        contract.status = new_status
        contract.save(update_fields=['status', 'updated_at'])
        
        # Return success response
        return Response({
            "message": _("Contract status updated successfully."),
            "old_status": old_status,
            "new_status": new_status
        })
    
    except Exception as e:
        logger.error(f"Error in update_contract_status: {str(e)}")
        return Response(
            {"error": _("An error occurred while updating the contract status.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== PAYMENT VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_list(request):
    """
    List payments with filtering options.
    
    Query parameters:
    - contract_id: Filter by related contract
    - payment_type: Filter by payment type
    - payment_method: Filter by payment method
    - status: Filter by payment status
    - payer_id: Filter by payer
    - payee_id: Filter by payee
    - min_amount: Filter by minimum amount
    - max_amount: Filter by maximum amount
    - sort_by: Sort by field (payment_date, amount, etc.)
    - sort_order: asc or desc
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        contract_id = request.query_params.get('contract_id')
        payment_type = request.query_params.get('payment_type')
        payment_method = request.query_params.get('payment_method')
        status = request.query_params.get('status')
        payer_id = request.query_params.get('payer_id')
        payee_id = request.query_params.get('payee_id')
        min_amount = request.query_params.get('min_amount')
        max_amount = request.query_params.get('max_amount')
        sort_by = request.query_params.get('sort_by', 'payment_date')
        sort_order = request.query_params.get('sort_order', 'desc')
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        
        # Base query - filter by user access
        user = request.user
        
        if user.is_staff:
            # Staff can see all payments
            queryset = Payment.objects.all()
        else:
            # Regular users can only see payments they're involved in
            queryset = Payment.objects.filter(
                Q(payer=user) | Q(payee=user)
            ).distinct()
        
        # Apply filters
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if payer_id and user.is_staff:
            queryset = queryset.filter(payer_id=payer_id)
        
        if payee_id and user.is_staff:
            queryset = queryset.filter(payee_id=payee_id)
        
        if min_amount:
            queryset = queryset.filter(amount__gte=float(min_amount))
        
        if max_amount:
            queryset = queryset.filter(amount__lte=float(max_amount))
        
        # Apply sorting
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['payment_date', 'amount', 'created_at', 'due_date']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = PaymentListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in payment_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching payments.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_create(request):
    """
    Create a new payment.
    Requires authentication and proper permissions.
    """
    try:
        # Initialize serializer with request data
        serializer = PaymentSerializer(data=request.data)
        
        # Validate data
        if serializer.is_valid():
            # Check if user is the payer
            user = request.user
            payer_id = serializer.validated_data.get('payer').id
            
            if payer_id != user.id and not user.is_staff:
                return Response(
                    {"error": _("You can only create payments where you are the payer.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate contract access
            contract_id = serializer.validated_data.get('contract').id
            contract = get_object_or_404(Contract, pk=contract_id)
            
            if not (
                user.is_staff or
                contract.buyer == user or
                contract.seller == user or
                contract.agent == user
            ):
                return Response(
                    {"error": _("You don't have access to this contract.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate payer and payee match contract roles for certain payment types
            payment_type = serializer.validated_data.get('payment_type')
            
            if payment_type in ['deposit', 'full_payment', 'installment']:
                if contract.buyer.id != payer_id:
                    return Response(
                        {"error": _(f"For {payment_type} payments, the payer must be the buyer.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if contract.seller.id != serializer.validated_data.get('payee').id:
                    return Response(
                        {"error": _(f"For {payment_type} payments, the payee must be the seller.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            elif payment_type == 'commission' and not user.is_staff:
                # Commissions are usually to agents/platform
                if contract.agent and contract.agent.id != serializer.validated_data.get('payee').id:
                    return Response(
                        {"error": _("For commission payments, the payee should be the agent.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Save payment
            payment = serializer.save()
            
            # Return success response
            return Response(
                PaymentDetailSerializer(payment).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in payment_create: {str(e)}")
        return Response(
            {"error": _("An error occurred while creating the payment.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_detail(request, pk):
    """
    Retrieve payment details.
    Requires authentication and proper access permissions.
    """
    try:
        # Get payment
        payment = get_object_or_404(Payment, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user.is_staff or
            payment.payer == user or
            payment.payee == user or
            payment.contract.agent == user
        ):
            return Response(
                {"error": _("You don't have permission to view this payment.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and return data
        serializer = PaymentDetailSerializer(payment)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in payment_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the payment details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request, pk):
    """
    Confirm a payment.
    Requires authentication as payee, agent, or staff.
    """
    try:
        # Get payment
        payment = get_object_or_404(Payment, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user.is_staff or
            payment.payee == user or
            (payment.contract and payment.contract.agent == user)
        ):
            return Response(
                {"error": _("You don't have permission to confirm this payment.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check payment status
        if payment.status != 'pending':
            return Response(
                {"error": _("Only pending payments can be confirmed.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Confirm payment
        result = payment.confirm_payment(user)
        
        if not result:
            return Response(
                {"error": _("Failed to confirm payment.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create a transaction record
        transaction_reference = f"PAY-{payment.payment_number}"
        
        transaction = Transaction.objects.create(
            transaction_number=f"T-{payment.payment_number}",
            transaction_type=payment.payment_type,
            description=f"Payment {payment.payment_number} confirmation",
            amount=payment.amount,
            currency=payment.currency,
            from_user=payment.payer,
            to_user=payment.payee,
            payment=payment,
            contract=payment.contract,
            transaction_date=timezone.now(),
            reference=transaction_reference,
            processed_by=user
        )
        
        # Mark transaction as completed
        transaction.mark_as_completed(user)
        
        # Return success response with updated payment
        serializer = PaymentDetailSerializer(payment)
        return Response({
            "message": _("Payment confirmed successfully."),
            "payment": serializer.data,
            "transaction_id": transaction.id
        })
    
    except Exception as e:
        logger.error(f"Error in confirm_payment: {str(e)}")
        return Response(
            {"error": _("An error occurred while confirming the payment.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_payments(request):
    """
    List all payments made or received by the current user.
    
    Query parameters:
    - direction: 'sent' for payments made, 'received' for payments received
    """
    try:
        # Get direction parameter
        direction = request.query_params.get('direction', 'all')
        
        # Get payments for current user
        user = request.user
        if direction == 'sent':
            queryset = Payment.objects.filter(payer=user)
        elif direction == 'received':
            queryset = Payment.objects.filter(payee=user)
        else:
            # All payments involving the user
            queryset = Payment.objects.filter(
                Q(payer=user) | Q(payee=user)
            ).distinct()
        
        # Apply sorting
        queryset = queryset.order_by('-payment_date')
        
        # Serialize data
        serializer = PaymentListSerializer(queryset, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in user_payments: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching your payments.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )













# ============== TRANSACTION VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_list(request):
    """
    List transactions with filtering options.
    
    Query parameters:
    - transaction_type: Filter by transaction type
    - from_user_id: Filter by sender
    - to_user_id: Filter by recipient
    - min_amount: Filter by minimum amount
    - max_amount: Filter by maximum amount
    - status: Filter by transaction status
    - payment_id: Filter by related payment
    - auction_id: Filter by related auction
    - contract_id: Filter by related contract
    - start_date: Filter by transactions after date (YYYY-MM-DD)
    - end_date: Filter by transactions before date (YYYY-MM-DD)
    - sort_by: Sort by field (transaction_date, amount, etc.)
    - sort_order: asc or desc
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        transaction_type = request.query_params.get('transaction_type')
        from_user_id = request.query_params.get('from_user_id')
        to_user_id = request.query_params.get('to_user_id')
        min_amount = request.query_params.get('min_amount')
        max_amount = request.query_params.get('max_amount')
        payment_id = request.query_params.get('payment_id')
        auction_id = request.query_params.get('auction_id')
        contract_id = request.query_params.get('contract_id')
        status = request.query_params.get('status')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        sort_by = request.query_params.get('sort_by', 'transaction_date')
        sort_order = request.query_params.get('sort_order', 'desc')
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        
        # Base query - filter by user access
        user = request.user
        
        if user.is_staff:
            # Staff can see all transactions
            queryset = Transaction.objects.all()
        else:
            # Regular users can only see transactions they're involved in
            queryset = Transaction.objects.filter(
                Q(from_user=user) | Q(to_user=user)
            ).distinct()
        
        # Apply filters
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        if from_user_id and user.is_staff:
            queryset = queryset.filter(from_user_id=from_user_id)
        
        if to_user_id and user.is_staff:
            queryset = queryset.filter(to_user_id=to_user_id)
        
        if min_amount:
            queryset = queryset.filter(amount__gte=float(min_amount))
        
        if max_amount:
            queryset = queryset.filter(amount__lte=float(max_amount))
        
        if payment_id:
            queryset = queryset.filter(payment_id=payment_id)
        
        if auction_id:
            queryset = queryset.filter(auction_id=auction_id)
        
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)
        
        # Apply sorting
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['transaction_date', 'amount', 'created_at', 'status']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = TransactionListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in transaction_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching transactions.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transaction_create(request):
    """
    Create a new transaction.
    Requires staff permissions or specific role-based permissions.
    """
    try:
        # Check permissions
        user = request.user
        if not user.is_staff:
            return Response(
                {"error": _("Only staff can create transactions directly.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Initialize serializer with request data
        serializer = TransactionSerializer(data=request.data)
        
        # Validate data
        if serializer.is_valid():
            # Set processed_by to current user if not provided
            if 'processed_by' not in serializer.validated_data:
                serializer.validated_data['processed_by'] = user
            
            # Save transaction
            transaction = serializer.save()
            
            # Return success response
            return Response(
                TransactionDetailSerializer(transaction).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in transaction_create: {str(e)}")
        return Response(
            {"error": _("An error occurred while creating the transaction.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_detail(request, pk):
    """
    Retrieve transaction details.
    Requires authentication and proper access permissions.
    """
    try:
        # Get transaction
        transaction = get_object_or_404(Transaction, pk=pk)
        
        # Check permissions
        user = request.user
        if not (
            user.is_staff or
            transaction.from_user == user or
            transaction.to_user == user
        ):
            return Response(
                {"error": _("You don't have permission to view this transaction.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and return data
        serializer = TransactionDetailSerializer(transaction)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in transaction_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the transaction details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_transaction_status(request, pk):
    """
    Update a transaction's status.
    Requires staff permissions.
    """
    try:
        # Check permissions
        user = request.user
        if not user.is_staff:
            return Response(
                {"error": _("Only staff can update transaction status.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get transaction
        transaction = get_object_or_404(Transaction, pk=pk)
        
        # Get new status from request
        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {"error": _("New status is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional reason for status update
        reason = request.data.get('reason')
        
        # Update status based on value
        if new_status == 'completed':
            result = transaction.mark_as_completed(user)
        elif new_status == 'failed':
            result = transaction.mark_as_failed(reason)
        else:
            # Try to validate the status transition
            try:
                transaction.validate_status_transition(
                    transaction.status,
                    new_status,
                    Transaction.STATUS_TRANSITIONS
                )
                
                transaction.status = new_status
                transaction.save(update_fields=['status', 'updated_at'])
                result = True
            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not result:
            return Response(
                {"error": _("Failed to update transaction status.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response
        return Response({
            "message": _("Transaction status updated successfully."),
            "old_status": transaction.status,
            "new_status": new_status
        })
    
    except Exception as e:
        logger.error(f"Error in update_transaction_status: {str(e)}")
        return Response(
            {"error": _("An error occurred while updating the transaction status.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_transactions(request):
    """
    List all transactions involving the current user.
    
    Query parameters:
    - direction: 'outgoing' for outgoing transactions, 'incoming' for incoming transactions
    """
    try:
        # Get direction parameter
        direction = request.query_params.get('direction', 'all')
        
        # Get transactions for current user
        user = request.user
        if direction == 'outgoing':
            queryset = Transaction.objects.filter(from_user=user)
        elif direction == 'incoming':
            queryset = Transaction.objects.filter(to_user=user)
        else:
            # All transactions involving the user
            queryset = Transaction.objects.filter(
                Q(from_user=user) | Q(to_user=user)
            ).distinct()
        
        # Apply sorting
        queryset = queryset.order_by('-transaction_date')
        
        # Serialize data
        serializer = TransactionListSerializer(queryset, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in user_transactions: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching your transactions.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== PROPERTY VIEW VIEWS ==============

@api_view(['GET'])
@permission_classes([AllowAny])
def property_view_list(request):
    """
    List property views with filtering options.
    
    Query parameters:
    - view_type: Filter by view type
    - location: Filter by location
    - auction_id: Filter by related auction
    - min_size: Filter by minimum size
    - max_size: Filter by maximum size
    - min_elevation: Filter by minimum elevation
    - max_elevation: Filter by maximum elevation
    - sort_by: Sort by field (created_at, size_sqm, etc.)
    - sort_order: asc or desc
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        view_type = request.query_params.get('view_type')
        location = request.query_params.get('location')
        auction_id = request.query_params.get('auction_id')
        min_size = request.query_params.get('min_size')
        max_size = request.query_params.get('max_size')
        min_elevation = request.query_params.get('min_elevation')
        max_elevation = request.query_params.get('max_elevation')
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        
        # Base query
        queryset = PropertyView.objects.all()
        
        # Filter by auction and ensure it's public or user has access
        if auction_id:
            queryset = queryset.filter(auction_id=auction_id)
            
            # For non-authenticated users, only show published auctions
            if not request.user.is_authenticated:
                queryset = queryset.filter(auction__is_published=True)
            else:
                user = request.user
                # For authenticated users, ensure they have access to private auctions
                if not user.is_staff:
                    queryset = queryset.filter(
                        Q(auction__is_published=True) |
                        Q(auction__created_by=user) |
                        Q(auction__auctioneer=user) |
                        Q(auction__invited_bidders=user)
                    ).distinct()
        
        # Apply view type filter
        if view_type:
            queryset = queryset.filter(view_type=view_type)
        
        # Apply location filter
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Apply size filters
        if min_size:
            queryset = queryset.filter(size_sqm__gte=float(min_size))
        
        if max_size:
            queryset = queryset.filter(size_sqm__lte=float(max_size))
        
        # Apply elevation filters
        if min_elevation:
            queryset = queryset.filter(elevation__gte=int(min_elevation))
        
        if max_elevation:
            queryset = queryset.filter(elevation__lte=int(max_elevation))
        
        # Apply sorting
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['created_at', 'size_sqm', 'elevation', 'view_type']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = PropertyViewListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in property_view_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching property views.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def property_view_create(request):
    """
    Create a new property view.
    Requires authentication and proper permissions.
    """
    try:
        # Check permissions
        user = request.user
        
        # Initialize serializer with request data
        serializer = PropertyViewSerializer(data=request.data)
        
        # Validate data
        if serializer.is_valid():
            # Validate auction ownership/access
            auction_id = serializer.validated_data.get('auction').id
            auction = get_object_or_404(Auction, pk=auction_id)
            
            if not (
                user.is_staff or
                auction.created_by == user or
                auction.auctioneer == user
            ):
                return Response(
                    {"error": _("You don't have permission to create property views for this auction.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Save property view
            property_view = serializer.save()
            
            # Return success response
            return Response(
                PropertyViewDetailSerializer(property_view).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in property_view_create: {str(e)}")
        return Response(
            {"error": _("An error occurred while creating the property view.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def property_view_detail(request, pk):
    """
    Retrieve property view details.
    Public endpoint with access control for private auctions.
    """
    try:
        # Get property view
        property_view = get_object_or_404(PropertyView, pk=pk)
        
        # Check access to associated auction if it's private
        auction = property_view.auction
        if auction.is_private:
            # Non-authenticated users can't access private auctions
            if not request.user.is_authenticated:
                return Response(
                    {"error": _("This property view is for a private auction.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if user has access to the private auction
            user = request.user
            if not (
                user.is_staff or
                auction.created_by == user or
                auction.auctioneer == user or
                auction.invited_bidders.filter(id=user.id).exists()
            ):
                return Response(
                    {"error": _("You don't have access to this property view.")},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Serialize and return data
        serializer = PropertyViewDetailSerializer(property_view)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in property_view_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the property view details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def property_view_update(request, pk):
    """
    Update a property view (PUT for full update, PATCH for partial update).
    Requires authentication and proper access permissions.
    """
    try:
        # Get property view
        property_view = get_object_or_404(PropertyView, pk=pk)
        
        # Check permissions
        user = request.user
        auction = property_view.auction
        
        if not (
            user.is_staff or
            auction.created_by == user or
            auction.auctioneer == user
        ):
            return Response(
                {"error": _("You don't have permission to update this property view.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Determine if this is a full or partial update
        partial = request.method == 'PATCH'
        
        # Initialize serializer with instance and data
        serializer = PropertyViewSerializer(
            property_view, 
            data=request.data, 
            partial=partial
        )
        
        # Validate data
        if serializer.is_valid():
            # Prevent changing auction
            if 'auction' in serializer.validated_data and serializer.validated_data['auction'] != property_view.auction:
                return Response(
                    {"error": _("You cannot change the auction associated with a property view.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save property view
            property_view = serializer.save()
            
            # Return updated data
            return Response(PropertyViewDetailSerializer(property_view).data)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in property_view_update: {str(e)}")
        return Response(
            {"error": _("An error occurred while updating the property view.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def property_view_delete(request, pk):
    """
    Delete a property view.
    Requires authentication and proper access permissions.
    """
    try:
        # Get property view
        property_view = get_object_or_404(PropertyView, pk=pk)
        
        # Check permissions
        user = request.user
        auction = property_view.auction
        
        if not (
            user.is_staff or
            auction.created_by == user
        ):
            return Response(
                {"error": _("You don't have permission to delete this property view.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete property view
        property_view.delete()
        
        # Return success response
        return Response(
            {"message": _("Property view deleted successfully.")},
            status=status.HTTP_204_NO_CONTENT
        )
    
    except Exception as e:
        logger.error(f"Error in property_view_delete: {str(e)}")
        return Response(
            {"error": _("An error occurred while deleting the property view.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def auction_property_views(request, auction_pk):
    """
    List all property views for a specific auction.
    Public endpoint with access control for private auctions.
    """
    try:
        # Get auction
        auction = get_object_or_404(Auction, pk=auction_pk)
        
        # Check access if auction is private
        if auction.is_private:
            # Non-authenticated users can't access private auctions
            if not request.user.is_authenticated:
                return Response(
                    {"error": _("This auction is private.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if user has access to the private auction
            user = request.user
            if not (
                user.is_staff or
                auction.created_by == user or
                auction.auctioneer == user or
                auction.invited_bidders.filter(id=user.id).exists()
            ):
                return Response(
                    {"error": _("You don't have access to this auction's property views.")},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Get property views for the auction
        queryset = PropertyView.objects.filter(auction=auction)
        
        # Serialize data
        serializer = PropertyViewListSerializer(queryset, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in auction_property_views: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the auction's property views.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== MESSAGE THREAD VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_thread_list(request):
    """
    List message threads with filtering options.
    
    Query parameters:
    - thread_type: Filter by thread type
    - status: Filter by thread status
    - property_id: Filter by related property
    - auction_id: Filter by related auction
    - contract_id: Filter by related contract
    - is_unread: Filter threads with unread messages (true/false)
    - sort_by: Sort by field (last_message_at, created_at, etc.)
    - sort_order: asc or desc
    - search: Search in subject
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        thread_type = request.query_params.get('thread_type')
        status = request.query_params.get('status')
        property_id = request.query_params.get('property_id')
        auction_id = request.query_params.get('auction_id')
        contract_id = request.query_params.get('contract_id')
        is_unread = request.query_params.get('is_unread')
        sort_by = request.query_params.get('sort_by', 'last_message_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        search = request.query_params.get('search')
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        
        # Get user's thread memberships - threads they are participants in
        user = request.user
        
        # Base query - filter by user participation
        if user.is_staff:
            # Staff can access all threads or filter by participant
            participant_id = request.query_params.get('participant_id')
            if participant_id:
                queryset = MessageThread.objects.filter(
                    thread_participants__user_id=participant_id,
                    thread_participants__is_active=True
                ).distinct()
            else:
                queryset = MessageThread.objects.all()
        else:
            # Regular users can only see threads they're participating in
            queryset = MessageThread.objects.filter(
                thread_participants__user=user,
                thread_participants__is_active=True
            ).distinct()
        
        # Apply filters
        if thread_type:
            queryset = queryset.filter(thread_type=thread_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if property_id:
            queryset = queryset.filter(related_property_id=property_id)
        
        if auction_id:
            queryset = queryset.filter(related_auction_id=auction_id)
        
        if contract_id:
            queryset = queryset.filter(related_contract_id=contract_id)
        
        if is_unread:
            is_unread_bool = is_unread.lower() == 'true'
            if is_unread_bool:
                # Get threads with unread messages for the user
                participant = ThreadParticipant.objects.filter(
                    thread__in=queryset,
                    user=user,
                    is_active=True
                )
                unread_thread_ids = [p.thread_id for p in participant if p.has_unread_messages]
                queryset = queryset.filter(id__in=unread_thread_ids)
        
        if search:
            queryset = queryset.filter(subject__icontains=search)
        
        # Apply sorting
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['last_message_at', 'created_at', 'thread_type', 'status']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        else:
            # Default sort by last message timestamp or creation date
            queryset = queryset.order_by('-last_message_at', '-created_at')
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = MessageThreadListSerializer(queryset, many=True, context={'user': user})
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in message_thread_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching message threads.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def message_thread_create(request):
    """
    Create a new message thread.
    Requires authentication.
    """
    try:
        # Initialize serializer with request data
        serializer = MessageThreadSerializer(data=request.data)
        
        # Validate data
        if serializer.is_valid():
            # Set creator to current user if not provided
            if 'creator' not in serializer.validated_data:
                serializer.validated_data['creator'] = request.user
            
            # Ensure user has access to related entities
            user = request.user
            
            related_property = serializer.validated_data.get('related_property')
            if related_property and not (
                user.is_staff or
                related_property.owner == user or
                user.has_role(Role.BUYER)  # Buyers can inquire about properties
            ):
                return Response(
                    {"error": _("You don't have permission to create a thread for this property.")},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            related_auction = serializer.validated_data.get('related_auction')
            if related_auction and not (
                user.is_staff or
                related_auction.created_by == user or
                related_auction.auctioneer == user or
                user.has_role(Role.BUYER)  # Buyers can inquire about auctions
            ):
                return Response(
                    {"error": _("You don't have permission to create a thread for this auction.")},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            related_contract = serializer.validated_data.get('related_contract')
            if related_contract and not (
                user.is_staff or
                related_contract.buyer == user or
                related_contract.seller == user or
                related_contract.agent == user
            ):
                return Response(
                    {"error": _("You don't have permission to create a thread for this contract.")},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Save thread
            thread = serializer.save()
            
            # Add creator as a participant
            thread.add_participant(user, user.get_primary_role())
            
            # Add other participants from the request
            participants = request.data.get('participants', [])
            for participant_data in participants:
                try:
                    participant_user_id = participant_data.get('user_id')
                    participant_user = CustomUser.objects.get(id=participant_user_id)
                    role_name = participant_data.get('role', 'member')
                    
                    # Get role from role name
                    try:
                        role = Role.objects.get(name=role_name)
                    except Role.DoesNotExist:
                        # Default to member if role doesn't exist
                        role = None
                    
                    thread.add_participant(participant_user, role)
                except CustomUser.DoesNotExist:
                    continue
            
            # Create initial message if provided
            initial_message = request.data.get('initial_message')
            if initial_message:
                Message.objects.create(
                    thread=thread,
                    sender=user,
                    content=initial_message,
                    message_type=thread.thread_type,
                    related_property=thread.related_property,
                    related_auction=thread.related_auction,
                    related_contract=thread.related_contract,
                )
            
            # Return success response
            return Response(
                MessageThreadDetailSerializer(thread, context={'user': user}).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in message_thread_create: {str(e)}")
        return Response(
            {"error": _("An error occurred while creating the message thread.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_thread_detail(request, pk):
    """
    Retrieve message thread details.
    Requires authentication and proper access permissions.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=pk)
        
        # Check permissions
        user = request.user
        is_participant = ThreadParticipant.objects.filter(
            thread=thread,
            user=user,
            is_active=True
        ).exists()
        
        if not (
            user.is_staff or
            is_participant
        ):
            return Response(
                {"error": _("You don't have permission to view this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Automatically mark messages as read for this user when viewing thread
        if is_participant:
            participant = ThreadParticipant.objects.get(thread=thread, user=user)
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_at', 'updated_at'])
        
        # Serialize and return data
        serializer = MessageThreadDetailSerializer(thread, context={'user': user})
        
        # Get recent messages for this thread
        messages = Message.objects.filter(thread=thread).order_by('-sent_at')[:20]
        messages_serializer = MessageListSerializer(messages, many=True)
        
        # Combine data for response
        response_data = serializer.data
        response_data['recent_messages'] = messages_serializer.data
        
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"Error in message_thread_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the thread details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def message_thread_update(request, pk):
    """
    Update a message thread (partial update only).
    Requires authentication and proper access permissions.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=pk)
        
        # Check permissions
        user = request.user
        is_creator = thread.creator == user
        is_participant = ThreadParticipant.objects.filter(
            thread=thread,
            user=user,
            is_active=True
        ).exists()
        
        if not (
            user.is_staff or
            is_creator
        ):
            return Response(
                {"error": _("You don't have permission to update this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow updating certain fields
        allowed_fields = ['subject', 'status']
        update_data = {}
        
        for field in allowed_fields:
            if field in request.data:
                update_data[field] = request.data[field]
        
        # Initialize serializer with instance and data
        serializer = MessageThreadSerializer(
            thread, 
            data=update_data, 
            partial=True
        )
        
        # Validate data
        if serializer.is_valid():
            # Save thread
            thread = serializer.save()
            
            # Return updated data
            return Response(MessageThreadDetailSerializer(thread, context={'user': user}).data)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(f"Error in message_thread_update: {str(e)}")
        return Response(
            {"error": _("An error occurred while updating the message thread.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close_thread(request, pk):
    """
    Close a message thread.
    Requires authentication and proper access permissions.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=pk)
        
        # Check permissions
        user = request.user
        is_creator = thread.creator == user
        
        if not (
            user.is_staff or
            is_creator
        ):
            return Response(
                {"error": _("You don't have permission to close this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check current status
        if thread.status == 'closed':
            return Response(
                {"error": _("This thread is already closed.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Close thread
        result = thread.close_thread()
        
        if not result:
            return Response(
                {"error": _("Failed to close thread.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response
        return Response({
            "message": _("Thread closed successfully."),
            "status": thread.status
        })
    
    except Exception as e:
        logger.error(f"Error in close_thread: {str(e)}")
        return Response(
            {"error": _("An error occurred while closing the thread.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reopen_thread(request, pk):
    """
    Reopen a closed message thread.
    Requires authentication and proper access permissions.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=pk)
        
        # Check permissions
        user = request.user
        is_creator = thread.creator == user
        
        if not (
            user.is_staff or
            is_creator
        ):
            return Response(
                {"error": _("You don't have permission to reopen this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check current status
        if thread.status != 'closed':
            return Response(
                {"error": _("This thread is not closed.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reopen thread
        result = thread.reopen_thread()
        
        if not result:
            return Response(
                {"error": _("Failed to reopen thread.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response
        return Response({
            "message": _("Thread reopened successfully."),
            "status": thread.status
        })
    
    except Exception as e:
        logger.error(f"Error in reopen_thread: {str(e)}")
        return Response(
            {"error": _("An error occurred while reopening the thread.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_participant(request, pk):
    """
    Add a participant to a message thread.
    Requires authentication and proper access permissions.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=pk)
        
        # Check permissions
        user = request.user
        is_creator = thread.creator == user
        
        if not (
            user.is_staff or
            is_creator
        ):
            return Response(
                {"error": _("You don't have permission to add participants to this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get user_id and role from request
        user_id = request.data.get('user_id')
        role_name = request.data.get('role', 'member')
        
        if not user_id:
            return Response(
                {"error": _("User ID is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user to add
        try:
            participant_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": _("User not found.")},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get role from role name
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            # Default to None if role doesn't exist
            role = None
        
        # Add participant
        participant = thread.add_participant(participant_user, role)
        
        # Return success response
        return Response({
            "message": _("Participant added successfully."),
            "participant": ThreadParticipantSerializer(participant).data
        })
    
    except Exception as e:
        logger.error(f"Error in add_participant: {str(e)}")
        return Response(
            {"error": _("An error occurred while adding the participant.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_thread(request, pk):
    """
    Leave a message thread.
    Requires authentication and proper participation.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=pk)
        
        # Check if user is a participant
        user = request.user
        is_participant = ThreadParticipant.objects.filter(
            thread=thread,
            user=user,
            is_active=True
        ).exists()
        
        if not is_participant:
            return Response(
                {"error": _("You are not a participant in this thread.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Leave thread
        result = thread.remove_participant(user)
        
        if not result:
            return Response(
                {"error": _("Failed to leave thread.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response
        return Response({
            "message": _("You have left the thread successfully.")
        })
    
    except Exception as e:
        logger.error(f"Error in leave_thread: {str(e)}")
        return Response(
            {"error": _("An error occurred while leaving the thread.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== MESSAGE VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_list(request, thread_pk):
    """
    List messages in a thread with filtering options.
    
    Query parameters:
    - sender_id: Filter by sender
    - message_type: Filter by message type
    - status: Filter by message status
    - is_system_message: Filter system messages (true/false)
    - is_important: Filter important messages (true/false)
    - start_date: Filter by messages after date (YYYY-MM-DD)
    - end_date: Filter by messages before date (YYYY-MM-DD)
    - search: Search in message content
    - has_attachments: Filter messages with attachments (true/false)
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=thread_pk)
        
        # Check permissions
        user = request.user
        is_participant = ThreadParticipant.objects.filter(
            thread=thread,
            user=user,
            is_active=True
        ).exists()
        
        if not (
            user.is_staff or
            is_participant
        ):
            return Response(
                {"error": _("You don't have permission to view messages in this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark thread as read for this user
        if is_participant:
            thread.mark_as_read_for_user(user)
        
        # Get query parameters
        sender_id = request.query_params.get('sender_id')
        message_type = request.query_params.get('message_type')
        status = request.query_params.get('status')
        is_system_message = request.query_params.get('is_system_message')
        is_important = request.query_params.get('is_important')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        search = request.query_params.get('search')
        has_attachments = request.query_params.get('has_attachments')
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        # Base query - get messages for this thread
        queryset = Message.objects.filter(thread=thread)
        
        # Apply filters
        if sender_id:
            queryset = queryset.filter(sender_id=sender_id)
        
        if message_type:
            queryset = queryset.filter(message_type=message_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if is_system_message:
            is_system_message_bool = is_system_message.lower() == 'true'
            queryset = queryset.filter(is_system_message=is_system_message_bool)
        
        if is_important:
            is_important_bool = is_important.lower() == 'true'
            queryset = queryset.filter(is_important=is_important_bool)
        
        if start_date:
            queryset = queryset.filter(sent_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(sent_at__lte=end_date)
        
        if search:
            queryset = queryset.filter(content__icontains=search)
        
        if has_attachments:
            # Filter messages with attachments
            # This is a simplification - in real implementation would need to parse JSON field
            has_attachments_bool = has_attachments.lower() == 'true'
            if has_attachments_bool:
                queryset = queryset.exclude(attachments='[]')
        
        # Apply sorting - messages in chronological order
        queryset = queryset.order_by('-sent_at')
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = MessageListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in message_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching messages.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, thread_pk):
    """
    Send a new message in a thread.
    Requires authentication and thread participation.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=thread_pk)
        
        # Check permissions
        user = request.user
        is_participant = ThreadParticipant.objects.filter(
            thread=thread,
            user=user,
            is_active=True
        ).exists()
        
        if not (
            user.is_staff or
            is_participant
        ):
            return Response(
                {"error": _("You don't have permission to send messages in this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if thread is closed
        if thread.status == 'closed' and not user.is_staff:
            return Response(
                {"error": _("This thread is closed.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get message content and other data
        content = request.data.get('content')
        if not content:
            return Response(
                {"error": _("Message content is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create message
        message_data = {
            'thread': thread,
            'sender': user,
            'content': content,
            'message_type': request.data.get('message_type', 'reply'),
            'is_important': request.data.get('is_important', False),
            'parent_message_id': request.data.get('parent_message_id'),
            'related_property': thread.related_property,
            'related_auction': thread.related_auction,
            'related_contract': thread.related_contract
        }
        
        # Handle attachments if provided
        attachments = request.data.get('attachments')
        if attachments:
            message_data['attachments'] = attachments
        
        # Create the message
        message = Message.objects.create(**message_data)
        
        # Create notifications for other thread participants
        for participant in thread.thread_participants.filter(is_active=True).exclude(user=user):
            # Skip muted threads
            if participant.is_muted:
                continue
                
            # Create notification
            Notification.objects.create(
                recipient=participant.user,
                notification_type='message',
                title=_("New message in {0}").format(thread.subject),
                content=content[:100] + ('...' if len(content) > 100 else ''),
                channel='app',
                related_message=message,
                icon='message-circle',
                action_url=f'/messages/threads/{thread.id}'
            )
        
        # Return success response
        serializer = MessageDetailSerializer(message)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return Response(
            {"error": _("An error occurred while sending the message.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_detail(request, pk):
    """
    Retrieve message details.
    Requires authentication and proper access permissions.
    """
    try:
        # Get message
        message = get_object_or_404(Message, pk=pk)
        
        # Check permissions
        user = request.user
        is_participant = ThreadParticipant.objects.filter(
            thread=message.thread,
            user=user,
            is_active=True
        ).exists()
        
        if not (
            user.is_staff or
            is_participant
        ):
            return Response(
                {"error": _("You don't have permission to view this message.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark message as read if user is not the sender
        if user != message.sender:
            message.mark_as_read(user)
        
        # Serialize and return data
        serializer = MessageDetailSerializer(message)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in message_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the message details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_message_as_read(request, pk):
    """
    Mark a message as read.
    Requires authentication and thread participation.
    """
    try:
        # Get message
        message = get_object_or_404(Message, pk=pk)
        
        # Check permissions
        user = request.user
        is_participant = ThreadParticipant.objects.filter(
            thread=message.thread,
            user=user,
            is_active=True
        ).exists()
        
        if not (
            user.is_staff or
            is_participant
        ):
            return Response(
                {"error": _("You don't have permission to mark this message.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Don't mark own messages
        if user == message.sender:
            return Response(
                {"error": _("You cannot mark your own messages as read.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark message as read
        result = message.mark_as_read(user)
        
        if not result:
            return Response(
                {"error": _("Failed to mark message as read.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response
        return Response({
            "message": _("Message marked as read successfully."),
            "status": message.status,
            "read_at": message.read_at
        })
    
    except Exception as e:
        logger.error(f"Error in mark_message_as_read: {str(e)}")
        return Response(
            {"error": _("An error occurred while marking the message as read.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request, thread_pk):
    """
    Mark all messages in a thread as read.
    Requires authentication and thread participation.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=thread_pk)
        
        # Check permissions
        user = request.user
        is_participant = ThreadParticipant.objects.filter(
            thread=thread,
            user=user,
            is_active=True
        ).exists()
        
        if not (
            user.is_staff or
            is_participant
        ):
            return Response(
                {"error": _("You don't have permission to mark messages in this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark all messages as read
        count = thread.mark_as_read_for_user(user)
        
        # Return success response
        return Response({
            "message": _("Marked {0} messages as read.").format(count),
            "count": count
        })
    
    except Exception as e:
        logger.error(f"Error in mark_all_as_read: {str(e)}")
        return Response(
            {"error": _("An error occurred while marking messages as read.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== THREAD PARTICIPANT VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def thread_participants(request, thread_pk):
    """
    List participants in a message thread.
    Requires authentication and thread participation.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=thread_pk)
        
        # Check permissions
        user = request.user
        is_participant = ThreadParticipant.objects.filter(
            thread=thread,
            user=user,
            is_active=True
        ).exists()
        
        if not (
            user.is_staff or
            is_participant
        ):
            return Response(
                {"error": _("You don't have permission to view participants in this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get participants
        queryset = ThreadParticipant.objects.filter(
            thread=thread,
            is_active=True
        )
        
        # Serialize data
        serializer = ThreadParticipantDetailSerializer(queryset, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in thread_participants: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching thread participants.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_mute(request, thread_pk):
    """
    Toggle mute status for a thread.
    Requires authentication and thread participation.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=thread_pk)
        
        # Check permissions
        user = request.user
        
        try:
            participant = ThreadParticipant.objects.get(
                thread=thread,
                user=user,
                is_active=True
            )
        except ThreadParticipant.DoesNotExist:
            return Response(
                {"error": _("You are not a participant in this thread.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Toggle mute status
        is_muted = participant.toggle_mute()
        
        # Return success response
        return Response({
            "message": _("Thread {0} successfully.").format(
                "muted" if is_muted else "unmuted"
            ),
            "is_muted": is_muted
        })
    
    except Exception as e:
        logger.error(f"Error in toggle_mute: {str(e)}")
        return Response(
            {"error": _("An error occurred while toggling mute status.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_participant_role(request, thread_pk, user_pk):
    """
    Set a participant's role in a thread.
    Requires authentication and thread ownership or staff permissions.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=thread_pk)
        
        # Check permissions
        user = request.user
        is_creator = thread.creator == user
        
        if not (
            user.is_staff or
            is_creator
        ):
            return Response(
                {"error": _("You don't have permission to modify participant roles.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get role from request
        role_name = request.data.get('role')
        if not role_name:
            return Response(
                {"error": _("Role name is required.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get participant
        try:
            participant = ThreadParticipant.objects.get(
                thread=thread,
                user_id=user_pk,
                is_active=True
            )
        except ThreadParticipant.DoesNotExist:
            return Response(
                {"error": _("Participant not found.")},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Assign role
        result = participant.assign_role(role_name)
        
        if not result:
            return Response(
                {"error": _("Role assignment failed. Role may not exist.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return success response
        return Response({
            "message": _("Role assigned successfully."),
            "role": role_name
        })
    
    except Exception as e:
        logger.error(f"Error in set_participant_role: {str(e)}")
        return Response(
            {"error": _("An error occurred while setting participant role.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_participant(request, thread_pk, user_pk):
    """
    Remove a participant from a thread.
    Requires authentication and thread ownership or staff permissions.
    """
    try:
        # Get message thread
        thread = get_object_or_404(MessageThread, pk=thread_pk)
        
        # Check permissions
        user = request.user
        is_creator = thread.creator == user
        
        if not (
            user.is_staff or
            is_creator
        ):
            return Response(
                {"error": _("You don't have permission to remove participants.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get user to remove
        try:
            remove_user = CustomUser.objects.get(id=user_pk)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": _("User not found.")},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Don't allow removing thread creator
        if remove_user == thread.creator:
            return Response(
                {"error": _("Cannot remove the thread creator.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove participant
        result = thread.remove_participant(remove_user)
        
        if not result:
            return Response(
                {"error": _("Failed to remove participant.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response
        return Response({
            "message": _("Participant removed successfully.")
        })
    
    except Exception as e:
        logger.error(f"Error in remove_participant: {str(e)}")
        return Response(
            {"error": _("An error occurred while removing the participant.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============== NOTIFICATION VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """
    List notifications with filtering options.
    
    Query parameters:
    - notification_type: Filter by notification type
    - is_read: Filter by read status (true/false)
    - channel: Filter by notification channel
    - start_date: Filter by notifications after date (YYYY-MM-DD)
    - end_date: Filter by notifications before date (YYYY-MM-DD)
    - property_id: Filter by related property
    - auction_id: Filter by related auction
    - contract_id: Filter by related contract
    - sort_by: Sort by field (created_at, etc.)
    - sort_order: asc or desc
    - limit: Limit number of results
    - offset: Offset for pagination
    """
    try:
        # Get query parameters
        notification_type = request.query_params.get('notification_type')
        is_read = request.query_params.get('is_read')
        channel = request.query_params.get('channel')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        property_id = request.query_params.get('property_id')
        auction_id = request.query_params.get('auction_id')
        contract_id = request.query_params.get('contract_id')
        sort_by = request.query_params.get('sort_by', 'created_at')
        sort_order = request.query_params.get('sort_order', 'desc')
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        # Base query - get notifications for current user
        user = request.user
        queryset = Notification.objects.filter(recipient=user)
        
        # Apply filters
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        if is_read:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        
        if channel:
            queryset = queryset.filter(channel=channel)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        if property_id:
            queryset = queryset.filter(related_property_id=property_id)
        
        if auction_id:
            queryset = queryset.filter(related_auction_id=auction_id)
        
        if contract_id:
            queryset = queryset.filter(related_contract_id=contract_id)
        
        # Apply sorting
        sort_prefix = '-' if sort_order == 'desc' else ''
        if sort_by in ['created_at', 'is_read', 'notification_type']:
            queryset = queryset.order_by(f"{sort_prefix}{sort_by}")
        
        # Count total results for pagination
        total_count = queryset.count()
        
        # Apply pagination
        queryset = queryset[offset:offset + limit]
        
        # Serialize data
        serializer = NotificationListSerializer(queryset, many=True)
        
        # Prepare response with pagination details
        response_data = {
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        }
        
        return Response(response_data)
    
    except ValueError as e:
        return Response(
            {"error": f"Invalid parameter: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(f"Error in notification_list: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching notifications.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_detail(request, pk):
    """
    Retrieve notification details.
    Requires authentication and proper access permissions.
    """
    try:
        # Get notification
        notification = get_object_or_404(Notification, pk=pk)
        
        # Check permissions
        if notification.recipient != request.user:
            return Response(
                {"error": _("You don't have permission to view this notification.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark notification as read if it isn't already
        if not notification.is_read:
            notification.mark_as_read()
        
        # Serialize and return data
        serializer = NotificationDetailSerializer(notification)
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error in notification_detail: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching the notification details.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, pk):
    """
    Mark a notification as read.
    Requires authentication and proper ownership.
    """
    try:
        # Get notification
        notification = get_object_or_404(Notification, pk=pk)
        
        # Check ownership
        if notification.recipient != request.user:
            return Response(
                {"error": _("You don't have permission to modify this notification.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already read
        if notification.is_read:
            return Response({
                "message": _("Notification is already marked as read."),
                "is_read": notification.is_read,
                "read_at": notification.read_at
            })
        
        # Mark as read
        result = notification.mark_as_read()
        
        if not result:
            return Response(
                {"error": _("Failed to mark notification as read.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return success response
        return Response({
            "message": _("Notification marked as read successfully."),
            "is_read": notification.is_read,
            "read_at": notification.read_at
        })
    
    except Exception as e:
        logger.error(f"Error in mark_notification_as_read: {str(e)}")
        return Response(
            {"error": _("An error occurred while marking the notification as read.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_as_read(request):
    """
    Mark all notifications as read for the current user.
    """
    try:
        # Get unread notifications for current user
        user = request.user
        unread_notifications = Notification.objects.filter(
            recipient=user,
            is_read=False
        )
        
        # Get count of unread notifications
        count = unread_notifications.count()
        
        # Update all to read
        now = timezone.now()
        unread_notifications.update(
            is_read=True,
            read_at=now
        )
        
        # Return success response
        return Response({
            "message": _("Marked {0} notifications as read.").format(count),
            "count": count
        })
    
    except Exception as e:
        logger.error(f"Error in mark_all_notifications_as_read: {str(e)}")
        return Response(
            {"error": _("An error occurred while marking notifications as read.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, pk):
    """
    Delete a notification.
    Requires authentication and proper ownership.
    """
    try:
        # Get notification
        notification = get_object_or_404(Notification, pk=pk)
        
        # Check ownership
        if notification.recipient != request.user:
            return Response(
                {"error": _("You don't have permission to delete this notification.")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete notification
        notification.delete()
        
        # Return success response
        return Response(
            {"message": _("Notification deleted successfully.")},
            status=status.HTTP_204_NO_CONTENT
        )
    
    except Exception as e:
        logger.error(f"Error in delete_notification: {str(e)}")
        return Response(
            {"error": _("An error occurred while deleting the notification.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_counts(request):
    """
    Get notification counts (total and unread) for the current user.
    """
    try:
        # Get counts for current user
        user = request.user
        total_count = Notification.objects.filter(recipient=user).count()
        unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
        
        # Get counts by notification type
        type_counts = Notification.objects.filter(recipient=user)\
            .values('notification_type')\
            .annotate(
                total=Count('id'),
                unread=Count('id', filter=Q(is_read=False))
            )
        
        # Return counts
        return Response({
            "total": total_count,
            "unread": unread_count,
            "by_type": type_counts
        })
    
    except Exception as e:
        logger.error(f"Error in notification_counts: {str(e)}")
        return Response(
            {"error": _("An error occurred while fetching notification counts.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )