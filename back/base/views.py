from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
import logging
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ValidationError  
from rest_framework.exceptions import PermissionDenied  

import json

from .models import (
    Property, 
    Auction, 
    Bid, Document, Contract,
    MessageThread, ThreadParticipant, Message, Notification,
    Media 
)
from .serializers import (
    PropertySerializer, 
    AuctionSerializer, 
    BidSerializer, DocumentSerializer, ContractSerializer, MessageThreadSerializer,
    ThreadParticipantSerializer, MessageSerializer, NotificationSerializer,
    MediaSerializer 
)
from .permissions import (
    IsAdminUser, IsVerifiedUser, HasRolePermission, IsPropertyOwner, IsAuctionParticipant,
    IsBidOwner, IsDocumentAuthorized, IsMessageParticipant, IsContractParty, ReadOnly,
    IsOwnerOrReadOnly, IsAdminOrReadOnly
)
from .decorators import (
    api_role_required, api_verified_user_required, api_permission_required,
    log_api_calls, timing_decorator
)
from .utils import (
    get_bid_increment_suggestions, check_auction_status, get_user_permissions,
    check_user_permission
)

# Set up logging for debugging
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Custom Pagination Classes
# -------------------------------------------------------------------------


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for most views"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class LargeResultsSetPagination(PageNumberPagination):
    """Pagination for views that might have many results"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

class SmallResultsSetPagination(PageNumberPagination):
    """Pagination for views with few items per page"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50






# -------------------------------------------------------------------------
# Property Views
# -------------------------------------------------------------------------



class PropertyListCreateView(generics.ListCreateAPIView):
    """
    List all properties or create a new property.

    GET: List all properties based on user role and permissions
    POST: Create a new property (requires verification)
    """
    serializer_class = PropertySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'status', 'city', 'is_published', 'is_featured', 'is_verified']
    search_fields = ['title', 'address', 'description', 'city', 'property_number', 'deed_number']
    ordering_fields = ['created_at', 'market_value', 'size_sqm', 'bedrooms', 'year_built']
    ordering = ['-is_featured', '-created_at']

    def get_permissions(self):
        """
        Dynamic permissions based on the action:
        - List: Any authenticated user can list properties
        - Create: Only verified users with proper permissions can create properties
        """
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method == 'POST':
            return [IsAuthenticated(), IsVerifiedUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Filter properties based on user role.
        - Admins see all properties
        - Sellers/Owners see their own properties and published ones
        - Other users see only published properties
        """
        user = self.request.user

        # Default queryset for safety
        base_queryset = Property.objects.all()

        try:
            # Admin sees all properties
            if user.has_role('admin'):
                return base_queryset

            # Sellers and owners see their own properties + published ones
            if user.has_role('seller') or user.has_role('owner'):
                own_properties = Q(owner=user)
                published_properties = Q(is_published=True)
                return base_queryset.filter(own_properties | published_properties)

            # Everyone else sees only published properties
            return base_queryset.filter(is_published=True)

        except Exception as e:
            logger.error(f"Error in PropertyListCreateView.get_queryset: {str(e)}")
            return Property.objects.none()

    @log_api_calls
    @api_verified_user_required
    def perform_create(self, serializer):
        """
        Create a new property with the current user as owner.
        Permissions are handled by permission classes and decorators.
        # TODO: Implement associating Media objects (images, etc.) after creation.
        """
        if not check_user_permission(self.request.user, 'add_property'):
            raise PermissionDenied(_("You do not have permission to create properties."))

        serializer.save(owner=self.request.user)
        logger.info(f"Property created by user {self.request.user.id}")

class PropertyDetailView(generics.RetrieveAPIView):
    """
    Retrieve a property using slug field (with Arabic support).

    GET: Get detailed information about a specific property
    """
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'  # This tells DRF to use slug instead of pk
    lookup_url_kwarg = 'slug'  # This is the URL parameter name

    def get_queryset(self):
        """
        Filter properties based on user role.
        - Admins see all properties
        - Sellers/Owners see their own properties and published ones
        - Other users see only published properties
        """
        user = self.request.user
        if user.has_role('admin'):
            return Property.objects.all()
        if user.has_role('seller') or user.has_role('owner'):
            own_properties = Q(owner=user)
            published_properties = Q(is_published=True)
            return Property.objects.filter(own_properties | published_properties)
        return Property.objects.filter(is_published=True)

    @timing_decorator
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to track property views and add custom data
        """
        instance = self.get_object()

        # Increment view count
        instance.view_count = getattr(instance, 'view_count', 0) + 1
        instance.save(update_fields=['view_count'])

        # Get standard serializer data
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Add additional context data if needed
        if hasattr(instance, 'auctions') and instance.auctions.exists():
            # Add active auctions info if any
            active_auctions = instance.auctions.filter(
                status__in=['scheduled', 'live'],
                is_published=True
            ).order_by('start_date')

            if active_auctions.exists():
                data['active_auction'] = {
                    'id': active_auctions[0].id,
                    'uuid': str(active_auctions[0].uuid),
                    'title': active_auctions[0].title,
                    'start_date': active_auctions[0].start_date,
                    'end_date': active_auctions[0].end_date,
                    'current_bid': active_auctions[0].current_bid,
                    'status': active_auctions[0].status,
                }

        # Log the view for analytics (optional)
        if hasattr(request, 'user') and request.user.is_authenticated:
            self._log_property_view(request, instance)

        return Response(data)

    def _log_property_view(self, request, property_obj):
        """
        Helper method to log property views for analytics
        """
        # Increment the view count on the property (already handled in retrieve method)

        # If the property is associated with active auctions, log a property view for the auction
        if hasattr(property_obj, 'auctions') and property_obj.auctions.filter(
                status__in=['scheduled', 'live'],
                is_published=True
            ).exists():

            from .models import PropertyView, Auction

            try:
                # Get the most relevant auction
                auction = property_obj.auctions.filter(
                    status__in=['scheduled', 'live'],
                    is_published=True
                ).order_by('start_date').first()

                if auction:
                    # Create a property view entry as a 'street' view type for basic tracking
                    PropertyView.objects.create(
                        auction=auction,
                        view_type='street',  # Using the existing view_type choices
                        address=property_obj.address,
                        location={
                            "source": "property_detail_view",
                            "timestamp": timezone.now().isoformat(),
                            "user_id": request.user.id if request.user.is_authenticated else None,
                            "ip_address": request.META.get('REMOTE_ADDR', ''),
                            "user_agent": request.META.get('HTTP_USER_AGENT', '')
                        }
                    )
            except Exception as e:
                # Log error but don't interrupt response
                logger.error(f"Failed to log property view: {str(e)}")

class PropertyEditView(generics.UpdateAPIView):
    """
    Update a property.

    PUT: Update all fields of a property
    PATCH: Update specific fields of a property
    """
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated, IsPropertyOwner]
    lookup_field = 'slug'

    @log_api_calls
    @api_verified_user_required
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @log_api_calls
    @api_verified_user_required
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class PropertyDeleteView(generics.DestroyAPIView):
    """
    Delete a property.

    DELETE: Remove a property (owner or admin only)
    """
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated, IsPropertyOwner]
    lookup_field = 'slug'

    @log_api_calls
    @api_verified_user_required
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

# -------------------------------------------------------------------------
# Auction Views
# -------------------------------------------------------------------------




class AuctionListCreateView(generics.ListCreateAPIView):
    """
    List all auctions or create a new auction.

    GET: List all accessible auctions based on user role
    POST: Create a new auction (requires verification and permission)
    """
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['auction_type', 'status', 'is_published', 'is_featured', 'is_private']
    search_fields = ['title', 'description', 'related_property__title']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'current_bid']
    ordering = ['-is_featured', '-start_date']

    def get_queryset(self):
        user = self.request.user
        if user.has_role('admin'):
            return Auction.objects.all()
        if user.has_role('seller') or user.has_role('owner'):
            own_auctions = Q(related_property__owner=user)
            public_auctions = Q(is_published=True, is_private=False)
            return Auction.objects.filter(own_auctions | public_auctions)
        return Auction.objects.filter(is_published=True, is_private=False)

    @log_api_calls
    @api_verified_user_required
    @api_permission_required('can_create_auction')
    def create(self, request, *args, **kwargs):
        property_id = request.data.get('related_property')
        if property_id:
            property_obj = get_object_or_404(Property, id=property_id)
            if not (request.user.has_role('admin') or property_obj.owner == request.user):
                return Response(
                    {'detail': _('You do not have permission to create an auction for this property.')},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().create(request, *args, **kwargs)


class AuctionDetailView(generics.RetrieveAPIView):
    """
    Retrieve an auction.

    GET: Get detailed information about a specific auction
    """
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user
        if user.has_role('admin'):
            return Auction.objects.all()
        if user.has_role('seller') or user.has_role('owner'):
            own_auctions = Q(related_property__owner=user)
            public_auctions = Q(is_published=True, is_private=False)
            bid_auctions = Q(is_private=True, bids__bidder=user)
            return Auction.objects.filter(own_auctions | public_auctions | bid_auctions).distinct()
        public_auctions = Q(is_published=True, is_private=False)
        bid_auctions = Q(is_private=True, bids__bidder=user)
        return Auction.objects.filter(public_auctions | bid_auctions).distinct()

    @timing_decorator
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        check_auction_status(instance)
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AuctionEditView(generics.UpdateAPIView):
    """
    Update an auction.

    PUT: Update all fields of an auction
    PATCH: Update specific fields of an auction
    """
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    lookup_field = 'slug'

    @log_api_calls
    @api_verified_user_required
    def update(self, request, *args, **kwargs):
        auction = self.get_object()
        if not (request.user.has_role('admin') or auction.related_property.owner == request.user):
            return Response(
                {'detail': _('You do not have permission to update this auction.')},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    @log_api_calls
    @api_verified_user_required
    def partial_update(self, request, *args, **kwargs):
        auction = self.get_object()
        if not (request.user.has_role('admin') or auction.related_property.owner == request.user):
            return Response(
                {'detail': _('You do not have permission to update this auction.')},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)


class AuctionDeleteView(generics.DestroyAPIView):
    """
    Delete an auction.

    DELETE: Remove an auction (admin only)
    """
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'slug'

    @log_api_calls
    @api_verified_user_required
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)



# -------------------------------------------------------------------------
# Bid Views
# -------------------------------------------------------------------------

class BidListCreateView(generics.ListCreateAPIView):
    """
    List all bids for an auction or create a new bid.

    GET: List all bids for a specific auction (filtered by user role)
    POST: Place a new bid on an auction (verified users only)
    """
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsVerifiedUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_auto_bid']
    ordering_fields = ['bid_time', 'bid_amount']
    ordering = ['-bid_time']

    def get_queryset(self):
        auction_id = self.kwargs.get('auction_id')
        user = self.request.user
        try:
            auction = Auction.objects.get(id=auction_id)
        except Auction.DoesNotExist:
            return Bid.objects.none()
        if user.has_role('admin') or auction.related_property.owner == user:
            return Bid.objects.filter(auction_id=auction_id)
        return Bid.objects.filter(auction_id=auction_id, bidder=user)

    @log_api_calls
    @api_verified_user_required
    def perform_create(self, serializer):
        auction_id = self.kwargs.get('auction_id')
        auction = get_object_or_404(Auction, id=auction_id)
        status = check_auction_status(auction)
        if status != 'live':
            raise PermissionDenied(
                _('Bids can only be placed on live auctions. Current status: {status}').format(status=status)
            )
            
            
        serializer.save(
            auction=auction,
            bidder=self.request.user,
            bid_time=timezone.now(),
            ip_address=self.request.META.get('REMOTE_ADDR', ''),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

class BidDetailView(generics.RetrieveAPIView):
    """
    Retrieve a bid.

    GET: Get details of a specific bid (owner or admin only)
    """
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsBidOwner]

class BidEditView(generics.UpdateAPIView):
    """
    Update a bid.

    PUT: Update all fields of a bid (admin only)
    PATCH: Update specific fields of a bid (admin only)
    """
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsBidOwner, IsAdminUser]

    @log_api_calls
    @api_role_required('admin')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @log_api_calls
    @api_role_required('admin')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class BidDeleteView(generics.DestroyAPIView):
    """
    Delete a bid.

    DELETE: Remove a bid (admin only)
    """
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @log_api_calls
    @api_role_required('admin')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class BidSuggestionsView(APIView):
    """
    Get bid increment suggestions for an auction.

    GET: Get bid increment suggestions for a specific auction
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, auction_id, format=None):
        auction = get_object_or_404(Auction, id=auction_id)
        suggestions = get_bid_increment_suggestions(
            auction.current_bid or auction.starting_bid,
            min_increment=auction.minimum_increment,
            count=3,
            factor=1.5
        )
        return Response({
            'auction_id': auction_id,
            'current_bid': auction.current_bid,
            'minimum_increment': auction.minimum_increment,
            'suggestions': suggestions
        })

# -------------------------------------------------------------------------
# Document Views
# -------------------------------------------------------------------------





class DocumentListCreateView(generics.ListCreateAPIView):
    """
    List all documents or create a new document.

    GET: List all accessible documents based on user role
    POST: Create a new document (verified users only)
    """
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsVerifiedUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type', 'verification_status', 'is_public']
    search_fields = ['title', 'description', 'document_number']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.has_role('admin'):
            return Document.objects.all()
        if user.has_role('legal'):
            own_documents = Q(uploaded_by=user)
            pending_documents = Q(verification_status='pending')
            public_documents = Q(is_public=True)
            return Document.objects.filter(own_documents | pending_documents | public_documents)
        own_documents = Q(uploaded_by=user)
        property_documents = Q(related_property__owner=user)
        auction_documents = Q(related_auction__related_property__owner=user)
        contract_seller_documents = Q(related_contract__seller=user)
        contract_buyer_documents = Q(related_contract__buyer=user)
        public_documents = Q(is_public=True)
        return Document.objects.filter(
            own_documents | property_documents | auction_documents |
            contract_seller_documents | contract_buyer_documents | public_documents
        ).distinct()

    @api_verified_user_required
    def perform_create(self, serializer):
        """
        Create a document, ensuring the user has permission.
        The document can be related to a Property or Auction.
        # TODO: Implement associating Media object (the actual file) after creation.
        """
        related_obj = None
        related_model_type = None

        if 'related_property' in self.request.data:
            related_obj = get_object_or_404(Property, id=self.request.data['related_property'])
            related_model_type = 'property'
        elif 'related_auction' in self.request.data:
            related_obj = get_object_or_404(Auction, id=self.request.data['related_auction'])
            related_model_type = 'auction'
        elif 'related_contract' in self.request.data:
            related_obj = get_object_or_404(Contract, id=self.request.data['related_contract'])
            related_model_type = 'contract'

        if related_model_type == 'property':
            if not (self.request.user.has_role('admin') or related_obj.owner == self.request.user):
                raise PermissionDenied(_('You do not have permission to create documents for this property.'))
        elif related_model_type == 'auction':
            if not (self.request.user.has_role('admin') or related_obj.related_property.owner == self.request.user):
                raise PermissionDenied(_('You do not have permission to create documents for this auction.'))
        elif related_model_type == 'contract':
            if not (self.request.user.has_role('admin') or related_obj.seller == self.request.user or related_obj.buyer == self.request.user):
                raise PermissionDenied(_('You do not have permission to create documents for this contract.'))

        serializer.save(uploaded_by=self.request.user)

class DocumentDetailView(generics.RetrieveAPIView):
    """
    Retrieve a document.

    GET: Get details of a specific document (with permission checks)
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsDocumentAuthorized]

class DocumentEditView(generics.UpdateAPIView):
    """
    Update a document.

    PUT: Update all fields of a document
    PATCH: Update specific fields of a document
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsDocumentAuthorized]

    @log_api_calls
    @api_verified_user_required
    def perform_update(self, serializer):
        instance = self.get_object()
        verification_status = serializer.validated_data.get('verification_status')
        if verification_status == 'verified' and instance.verification_status != 'verified':
            if self.request.user.has_role('admin') or self.request.user.has_role('legal'):
                serializer.save(
                    verified_by=self.request.user,
                    verification_date=timezone.now()
                )
            else:
                self.permission_denied(
                    self.request,
                    message=_('Only admin or legal users can verify documents.')
                )
        else:
            serializer.save()

    @log_api_calls
    @api_verified_user_required
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @log_api_calls
    @api_verified_user_required
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class DocumentDeleteView(generics.DestroyAPIView):
    """
    Delete a document.

    DELETE: Remove a document (with permission checks)
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsDocumentAuthorized]

    @log_api_calls
    @api_verified_user_required
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

# -------------------------------------------------------------------------
# Contract Views
# -------------------------------------------------------------------------




class ContractListCreateView(generics.ListCreateAPIView):
    """
    List all contracts or create a new contract.

    GET: List all accessible contracts based on user role
    POST: Create a new contract (verified users only)
    """
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsVerifiedUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'is_verified']
    search_fields = ['title', 'description', 'contract_number']
    ordering_fields = ['contract_date', 'total_amount', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.has_role('admin'):
            return Contract.objects.all()
        if user.has_role('legal'):
            legal_contracts = Q(is_verified=False)
            user_contracts = Q(buyer=user) | Q(seller=user)
            return Contract.objects.filter(legal_contracts | user_contracts)
        return Contract.objects.filter(Q(buyer=user) | Q(seller=user))

    @log_api_calls
    @api_verified_user_required
    def create(self, request, *args, **kwargs):
        property_id = request.data.get('related_property')
        if property_id:
            property_obj = get_object_or_404(Property, id=property_id)
            if not (request.user.has_role('admin') or property_obj.owner == request.user):
                return Response(
                    {'detail': _('You do not have permission to create a contract for this property.')},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().create(request, *args, **kwargs)

class ContractDetailView(generics.RetrieveAPIView):
    """
    Retrieve a contract.

    GET: Get details of a specific contract (parties or admin only)
    """
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsContractParty]

class ContractEditView(generics.UpdateAPIView):
    """
    Update a contract.

    PUT: Update all fields of a contract
    PATCH: Update specific fields of a contract
    """
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsContractParty]

    @log_api_calls
    @api_verified_user_required
    def perform_update(self, serializer):
        instance = self.get_object()
        data = serializer.validated_data
        user = self.request.user
        is_verified = data.get('is_verified')
        if is_verified and not instance.is_verified:
            if user.has_role('admin') or user.has_role('legal'):
                serializer.save(
                    verified_by=user,
                    verification_date=timezone.now()
                )
                return
            else:
                self.permission_denied(
                    self.request,
                    message=_('Only admin or legal users can verify contracts.')
                )
        buyer_signed = data.get('buyer_signed')
        seller_signed = data.get('seller_signed')
        if buyer_signed and not instance.buyer_signed and user == instance.buyer:
            serializer.save(buyer_signed_date=timezone.now())
            return
        if seller_signed and not instance.seller_signed and user == instance.seller:
            serializer.save(seller_signed_date=timezone.now())
            return
        serializer.save()

    @log_api_calls
    @api_verified_user_required
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @log_api_calls
    @api_verified_user_required
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class ContractDeleteView(generics.DestroyAPIView):
    """
    Delete a contract.

    DELETE: Remove a contract (admin only)
    """
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @log_api_calls
    @api_role_required('admin')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

# -------------------------------------------------------------------------
# Message Thread Views
# -------------------------------------------------------------------------



class MessageThreadListCreateView(generics.ListCreateAPIView):
    """
    List all message threads or create a new thread.

    GET: List all threads where the user is a participant
    POST: Create a new message thread
    """
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['thread_type', 'status', 'is_private', 'is_system_thread']
    search_fields = ['subject']
    ordering_fields = ['last_message_at', 'created_at']
    ordering = ['-last_message_at']

    def get_queryset(self):
        user = self.request.user
        if user.has_role('admin'):
            return MessageThread.objects.all()
        return MessageThread.objects.filter(participants__user=user, participants__is_active=True)

    @api_verified_user_required
    def perform_create(self, serializer):
        thread = serializer.save(creator=self.request.user)
        if not thread.participants.filter(user=self.request.user).exists():
            ThreadParticipant.objects.create(
                thread=thread,
                user=self.request.user,
                is_active=True
            )

class MessageThreadDetailView(generics.RetrieveAPIView):
    """
    Retrieve a message thread.

    GET: Get details of a specific message thread (participants only)
    """
    queryset = MessageThread.objects.all()
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]

class MessageThreadEditView(generics.UpdateAPIView):
    """
    Update a message thread.

    PUT: Update all fields of a message thread
    PATCH: Update specific fields of a message thread
    """
    queryset = MessageThread.objects.all()
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]

    @api_verified_user_required
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @api_verified_user_required
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class MessageThreadDeleteView(generics.DestroyAPIView):
    """
    Delete a message thread.

    DELETE: Remove a message thread (admin only)
    """
    queryset = MessageThread.objects.all()
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @log_api_calls
    @api_role_required('admin')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class ThreadParticipantListView(generics.ListCreateAPIView):
    """
    List all participants in a thread or add a new participant.

    GET: List all participants in a specific thread
    POST: Add a new participant to a thread
    """
    serializer_class = ThreadParticipantSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        thread_id = self.kwargs.get('thread_id')
        return ThreadParticipant.objects.filter(thread_id=thread_id)

    @api_verified_user_required
    def perform_create(self, serializer):
        thread = get_object_or_404(MessageThread, id=self.kwargs.get('thread_id'))
        if not self.request.user.has_role('admin') and thread.creator != self.request.user:
            self.permission_denied(
                self.request,
                message=_('Only the thread creator or an admin can add participants.')
            )
        serializer.save(thread=thread)

class ThreadParticipantDetailView(generics.RetrieveAPIView):
    """
    Retrieve a thread participant.

    GET: Get details of a specific thread participant
    """
    queryset = ThreadParticipant.objects.all()
    serializer_class = ThreadParticipantSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]

class ThreadParticipantEditView(generics.UpdateAPIView):
    """
    Update a thread participant.

    PUT: Update all fields of a thread participant (admin only)
    PATCH: Update specific fields of a thread participant (admin only)
    """
    queryset = ThreadParticipant.objects.all()
    serializer_class = ThreadParticipantSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @api_verified_user_required
    @api_role_required('admin')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @api_verified_user_required
    @api_role_required('admin')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class ThreadParticipantDeleteView(generics.DestroyAPIView):
    """
    Delete a thread participant.

    DELETE: Remove a thread participant (admin only)
    """
    queryset = ThreadParticipant.objects.all()
    serializer_class = ThreadParticipantSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @log_api_calls
    @api_verified_user_required
    @api_role_required('admin')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class MessageListCreateView(generics.ListCreateAPIView):
    """
    List all messages in a thread or create a new message.

    GET: List all messages in a specific thread
    POST: Create a new message in a thread
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['message_type', 'status', 'is_system_message', 'is_important']
    ordering_fields = ['sent_at']
    ordering = ['sent_at']

    def get_queryset(self):
        thread_id = self.kwargs.get('thread_id')
        thread = get_object_or_404(MessageThread, id=thread_id)
        participant = thread.participants.filter(user=self.request.user, is_active=True).first()
        if participant:
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_at'])
        return Message.objects.filter(thread_id=thread_id)

    @api_verified_user_required
    def perform_create(self, serializer):
        thread = get_object_or_404(MessageThread, id=self.kwargs.get('thread_id'))
        if thread.status != 'active':
            self.permission_denied(
                self.request,
                message=_('Messages can only be sent in active threads.')
            )
        serializer.save(
            thread=thread,
            sender=self.request.user,
            sent_at=timezone.now()
        )

class MessageDetailView(generics.RetrieveAPIView):
    """
    Retrieve a message.

    GET: Get details of a specific message
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]

    @timing_decorator
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.sender != request.user and instance.status != 'read':
            instance.status = 'read'
            instance.read_at = timezone.now()
            instance.save(update_fields=['status', 'read_at'])
        return super().retrieve(request, *args, **kwargs)

class MessageEditView(generics.UpdateAPIView):
    """
    Update a message.

    PUT: Update all fields of a message (admin only)
    PATCH: Update specific fields of a message (admin only)
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @api_verified_user_required
    @api_role_required('admin')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @api_verified_user_required
    @api_role_required('admin')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class MessageDeleteView(generics.DestroyAPIView):
    """
    Delete a message.

    DELETE: Remove a message (admin only)
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @log_api_calls
    @api_verified_user_required
    @api_role_required('admin')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

# -------------------------------------------------------------------------
# Notification Views
# -------------------------------------------------------------------------





class NotificationListView(generics.ListAPIView):
    """
    List all notifications for the current user.

    GET: List all notifications for the authenticated user
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'is_read', 'is_sent', 'is_important']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

class NotificationDetailView(generics.RetrieveAPIView):
    """
    Retrieve a notification.

    GET: Get details of a specific notification and mark it as read
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @timing_decorator
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_read:
            instance.is_read = True
            instance.read_at = timezone.now()
            instance.save(update_fields=['is_read', 'read_at'])
        return super().retrieve(request, *args, **kwargs)

class NotificationEditView(generics.UpdateAPIView):
    """
    Update a notification.

    PUT: Update all fields of a notification
    PATCH: Update specific fields of a notification
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @api_verified_user_required
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @api_verified_user_required
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class NotificationDeleteView(generics.DestroyAPIView):
    """
    Delete a notification.

    DELETE: Remove a notification
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @log_api_calls
    @api_verified_user_required
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

