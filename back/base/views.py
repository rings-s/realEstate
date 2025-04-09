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

from .models import (
    Property, PropertyImage, Auction, AuctionImage, Bid, Document, Contract,
    MessageThread, ThreadParticipant, Message, PropertyView, Notification
)
from .serializers import (
    PropertySerializer, PropertyImageSerializer, AuctionSerializer, AuctionImageSerializer,
    BidSerializer, DocumentSerializer, ContractSerializer, MessageThreadSerializer,
    ThreadParticipantSerializer, MessageSerializer, PropertyViewSerializer, NotificationSerializer
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
    """
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'status', 'city', 'is_published', 'is_featured', 'is_verified']
    search_fields = ['title', 'address', 'description', 'city', 'property_number']
    ordering_fields = ['created_at', 'market_value', 'size_sqm', 'bedrooms', 'year_built']
    ordering = ['-is_featured', '-created_at']

    def get_queryset(self):
        """
        Return different querysets based on user role and permissions.
        - Admin users can see all properties
        - Property owners can see their own properties
        - Other users can only see published properties
        """
        user = self.request.user

        # Admin users can see all properties
        if user.has_role('admin'):
            return Property.objects.all()

        # Property owners can see their own properties
        if user.has_role('seller') or user.has_role('owner'):
            own_properties = Q(owner=user)
            published_properties = Q(is_published=True)
            return Property.objects.filter(own_properties | published_properties)

        # Other users can only see published properties
        return Property.objects.filter(is_published=True)

    def perform_create(self, serializer):
        """Set the owner to the current user when creating a property"""
        serializer.save(owner=self.request.user)

    @log_api_calls
    def create(self, request, *args, **kwargs):
        """Override create to add logging"""
        return super().create(request, *args, **kwargs)


class PropertyDetailView(generics.RetrieveAPIView):
    """
    Retrieve a property.
    """
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        """
        Return different querysets based on user role and permissions.
        """
        user = self.request.user

        # Admin users can see all properties
        if user.has_role('admin'):
            return Property.objects.all()

        # Property owners can see their own properties
        if user.has_role('seller') or user.has_role('owner'):
            own_properties = Q(owner=user)
            published_properties = Q(is_published=True)
            return Property.objects.filter(own_properties | published_properties)

        # Other users can only see published properties
        return Property.objects.filter(is_published=True)


class PropertyEditView(generics.UpdateAPIView):
    """
    Update a property.
    """
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated, IsPropertyOwner]
    lookup_field = 'slug'

    @api_verified_user_required
    def update(self, request, *args, **kwargs):
        """Override update to add verification check"""
        return super().update(request, *args, **kwargs)

    @api_verified_user_required
    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to add verification check"""
        return super().partial_update(request, *args, **kwargs)


class PropertyDeleteView(generics.DestroyAPIView):
    """
    Delete a property.
    """
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated, IsPropertyOwner]
    lookup_field = 'slug'

    @api_verified_user_required
    def destroy(self, request, *args, **kwargs):
        """Override destroy to add verification check"""
        return super().destroy(request, *args, **kwargs)


class PropertyImageListCreateView(generics.ListCreateAPIView):
    """
    List all images for a property or create a new image.
    """
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get images for the specified property"""
        property_id = self.kwargs.get('property_id')
        return PropertyImage.objects.filter(property_id=property_id).order_by('order', '-is_primary')

    def perform_create(self, serializer):
        """Set the property when creating an image"""
        property_obj = get_object_or_404(Property, id=self.kwargs.get('property_id'))

        # Check if user has permission to add images
        if not (self.request.user.has_role('admin') or property_obj.owner == self.request.user):
            self.permission_denied(self.request, message=_('You do not have permission to add images to this property.'))

        serializer.save(property=property_obj)


class PropertyImageDetailView(generics.RetrieveAPIView):
    """
    Retrieve a property image.
    """
    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAuthenticated]


class PropertyImageEditView(generics.UpdateAPIView):
    """
    Update a property image.
    """
    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_owner(self, obj):
        """Get the owner of the property image"""
        return obj.property.owner


class PropertyImageDeleteView(generics.DestroyAPIView):
    """
    Delete a property image.
    """
    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_owner(self, obj):
        """Get the owner of the property image"""
        return obj.property.owner


# -------------------------------------------------------------------------
# Auction Views
# -------------------------------------------------------------------------

class AuctionListCreateView(generics.ListCreateAPIView):
    """
    List all auctions or create a new auction.
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
        """
        Return different querysets based on user role and permissions.
        """
        user = self.request.user

        # Admin users can see all auctions
        if user.has_role('admin'):
            return Auction.objects.all()

        # Property owners can see auctions related to their properties
        if user.has_role('seller') or user.has_role('owner'):
            own_auctions = Q(related_property__owner=user)
            public_auctions = Q(is_published=True, is_private=False)
            return Auction.objects.filter(own_auctions | public_auctions)

        # Other users can only see published, non-private auctions
        return Auction.objects.filter(is_published=True, is_private=False)

    @api_verified_user_required
    @api_permission_required('can_create_auction')
    def create(self, request, *args, **kwargs):
        """Override create to add permission check"""
        property_id = request.data.get('related_property')
        if property_id:
            property_obj = get_object_or_404(Property, id=property_id)

            # Check if user has permission to create an auction for this property
            if not (request.user.has_role('admin') or property_obj.owner == request.user):
                return Response(
                    {'detail': _('You do not have permission to create an auction for this property.')},
                    status=status.HTTP_403_FORBIDDEN
                )

        return super().create(request, *args, **kwargs)


class AuctionDetailView(generics.RetrieveAPIView):
    """
    Retrieve an auction.
    """
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        """
        Return different querysets based on user role and permissions.
        """
        user = self.request.user

        # Admin users can see all auctions
        if user.has_role('admin'):
            return Auction.objects.all()

        # Property owners can see auctions related to their properties
        if user.has_role('seller') or user.has_role('owner'):
            own_auctions = Q(related_property__owner=user)
            public_auctions = Q(is_published=True, is_private=False)
            # Private auctions where user has placed a bid
            bid_auctions = Q(is_private=True, bids__bidder=user)
            return Auction.objects.filter(own_auctions | public_auctions | bid_auctions).distinct()

        # Other users can only see published, non-private auctions, or private auctions they've bid on
        public_auctions = Q(is_published=True, is_private=False)
        bid_auctions = Q(is_private=True, bids__bidder=user)
        return Auction.objects.filter(public_auctions | bid_auctions).distinct()

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to update auction status and increment view count"""
        instance = self.get_object()

        # Update auction status
        check_auction_status(instance)

        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AuctionEditView(generics.UpdateAPIView):
    """
    Update an auction.
    """
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    lookup_field = 'slug'

    @api_verified_user_required
    def update(self, request, *args, **kwargs):
        """Override update to add verification check"""
        auction = self.get_object()

        # Check if user has permission to update this auction
        if not (request.user.has_role('admin') or auction.related_property.owner == request.user):
            return Response(
                {'detail': _('You do not have permission to update this auction.')},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    @api_verified_user_required
    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to add verification check"""
        auction = self.get_object()

        # Check if user has permission to update this auction
        if not (request.user.has_role('admin') or auction.related_property.owner == request.user):
            return Response(
                {'detail': _('You do not have permission to update this auction.')},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().partial_update(request, *args, **kwargs)


class AuctionDeleteView(generics.DestroyAPIView):
    """
    Delete an auction.
    """
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'slug'


class AuctionImageListCreateView(generics.ListCreateAPIView):
    """
    List all images for an auction or create a new image.
    """
    serializer_class = AuctionImageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get images for the specified auction"""
        auction_id = self.kwargs.get('auction_id')
        return AuctionImage.objects.filter(auction_id=auction_id).order_by('order', '-is_primary')

    def perform_create(self, serializer):
        """Set the auction when creating an image"""
        auction = get_object_or_404(Auction, id=self.kwargs.get('auction_id'))

        # Check if user has permission to add images
        if not (self.request.user.has_role('admin') or auction.related_property.owner == self.request.user):
            self.permission_denied(self.request, message=_('You do not have permission to add images to this auction.'))

        serializer.save(auction=auction)


class AuctionImageDetailView(generics.RetrieveAPIView):
    """
    Retrieve an auction image.
    """
    queryset = AuctionImage.objects.all()
    serializer_class = AuctionImageSerializer
    permission_classes = [IsAuthenticated]


class AuctionImageEditView(generics.UpdateAPIView):
    """
    Update an auction image.
    """
    queryset = AuctionImage.objects.all()
    serializer_class = AuctionImageSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class AuctionImageDeleteView(generics.DestroyAPIView):
    """
    Delete an auction image.
    """
    queryset = AuctionImage.objects.all()
    serializer_class = AuctionImageSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


# -------------------------------------------------------------------------
# Bid Views
# -------------------------------------------------------------------------

class BidListCreateView(generics.ListCreateAPIView):
    """
    List all bids for an auction or create a new bid.
    """
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsVerifiedUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_auto_bid']
    ordering_fields = ['bid_time', 'bid_amount']
    ordering = ['-bid_time']

    def get_queryset(self):
        """Get bids for the specified auction"""
        auction_id = self.kwargs.get('auction_id')
        user = self.request.user

        # Get the auction
        try:
            auction = Auction.objects.get(id=auction_id)
        except Auction.DoesNotExist:
            return Bid.objects.none()

        # Admin users and property owners can see all bids
        if user.has_role('admin') or auction.related_property.owner == user:
            return Bid.objects.filter(auction_id=auction_id)

        # Other users can only see their own bids
        return Bid.objects.filter(auction_id=auction_id, bidder=user)

    @api_verified_user_required
    def perform_create(self, serializer):
        """Set the auction and bidder when creating a bid"""
        auction_id = self.kwargs.get('auction_id')
        auction = get_object_or_404(Auction, id=auction_id)

        # Update auction status
        status = check_auction_status(auction)

        # Check if auction is live
        if status != 'live':
            self.permission_denied(
                self.request,
                message=_('Bids can only be placed on live auctions. Current status: {status}').format(status=status)
            )

        # Save the bid
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
    """
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsBidOwner]


class BidEditView(generics.UpdateAPIView):
    """
    Update a bid.
    """
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsBidOwner, IsAdminUser]

    @api_role_required('admin')
    def update(self, request, *args, **kwargs):
        """Only admin users can update bids"""
        return super().update(request, *args, **kwargs)

    @api_role_required('admin')
    def partial_update(self, request, *args, **kwargs):
        """Only admin users can update bids"""
        return super().partial_update(request, *args, **kwargs)


class BidDeleteView(generics.DestroyAPIView):
    """
    Delete a bid.
    """
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class BidSuggestionsView(APIView):
    """
    Get bid increment suggestions for an auction.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, auction_id, format=None):
        """Get bid increment suggestions"""
        auction = get_object_or_404(Auction, id=auction_id)

        # Get suggestions
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
        """
        Return different querysets based on user role and permissions.
        """
        user = self.request.user

        # Admin users can see all documents
        if user.has_role('admin'):
            return Document.objects.all()

        # Legal users can see documents pending verification
        if user.has_role('legal'):
            own_documents = Q(uploaded_by=user)
            pending_documents = Q(verification_status='pending')
            public_documents = Q(is_public=True)
            return Document.objects.filter(own_documents | pending_documents | public_documents)

        # Property owners can see documents related to their properties
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

    def perform_create(self, serializer):
        """Set the uploaded_by to the current user when creating a document"""
        serializer.save(uploaded_by=self.request.user)


class DocumentDetailView(generics.RetrieveAPIView):
    """
    Retrieve a document.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsDocumentAuthorized]


class DocumentEditView(generics.UpdateAPIView):
    """
    Update a document.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsDocumentAuthorized]

    def perform_update(self, serializer):
        """
        Handle verification status changes
        """
        instance = self.get_object()
        verification_status = serializer.validated_data.get('verification_status')

        # If verification status is changing to 'verified', set verification details
        if verification_status == 'verified' and instance.verification_status != 'verified':
            if self.request.user.has_role('admin') or self.request.user.has_role('legal'):
                serializer.save(
                    verified_by=self.request.user,
                    verification_date=timezone.now()
                )
            else:
                # Non-authorized users can't verify documents
                self.permission_denied(
                    self.request,
                    message=_('Only admin or legal users can verify documents.')
                )
        else:
            serializer.save()


class DocumentDeleteView(generics.DestroyAPIView):
    """
    Delete a document.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsDocumentAuthorized]


# -------------------------------------------------------------------------
# Contract Views
# -------------------------------------------------------------------------

class ContractListCreateView(generics.ListCreateAPIView):
    """
    List all contracts or create a new contract.
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
        """
        Return different querysets based on user role and permissions.
        """
        user = self.request.user

        # Admin users can see all contracts
        if user.has_role('admin'):
            return Contract.objects.all()

        # Legal users can see contracts they need to verify
        if user.has_role('legal'):
            legal_contracts = Q(is_verified=False)
            user_contracts = Q(buyer=user) | Q(seller=user)
            return Contract.objects.filter(legal_contracts | user_contracts)

        # Users can see contracts where they are buyer or seller
        return Contract.objects.filter(Q(buyer=user) | Q(seller=user))

    @api_verified_user_required
    def create(self, request, *args, **kwargs):
        """Create a contract with validation"""
        property_id = request.data.get('related_property')

        if property_id:
            property_obj = get_object_or_404(Property, id=property_id)

            # Check if user has permission to create a contract for this property
            if not (request.user.has_role('admin') or property_obj.owner == request.user):
                return Response(
                    {'detail': _('You do not have permission to create a contract for this property.')},
                    status=status.HTTP_403_FORBIDDEN
                )

        return super().create(request, *args, **kwargs)


class ContractDetailView(generics.RetrieveAPIView):
    """
    Retrieve a contract.
    """
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsContractParty]


class ContractEditView(generics.UpdateAPIView):
    """
    Update a contract.
    """
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsContractParty]

    def perform_update(self, serializer):
        """
        Handle verification status changes and signatures
        """
        instance = self.get_object()
        data = serializer.validated_data
        user = self.request.user

        # Handle verification
        is_verified = data.get('is_verified')
        if is_verified and not instance.is_verified:
            if user.has_role('admin') or user.has_role('legal'):
                serializer.save(
                    verified_by=user,
                    verification_date=timezone.now()
                )
                return
            else:
                # Non-authorized users can't verify contracts
                self.permission_denied(
                    self.request,
                    message=_('Only admin or legal users can verify contracts.')
                )

        # Handle signatures
        buyer_signed = data.get('buyer_signed')
        seller_signed = data.get('seller_signed')

        if buyer_signed and not instance.buyer_signed and user == instance.buyer:
            serializer.save(buyer_signed_date=timezone.now())
            return

        if seller_signed and not instance.seller_signed and user == instance.seller:
            serializer.save(seller_signed_date=timezone.now())
            return

        serializer.save()


class ContractDeleteView(generics.DestroyAPIView):
    """
    Delete a contract.
    """
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


# -------------------------------------------------------------------------
# Message Thread Views
# -------------------------------------------------------------------------

class MessageThreadListCreateView(generics.ListCreateAPIView):
    """
    List all message threads or create a new thread.
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
        """
        Return threads where the user is a participant
        """
        user = self.request.user

        # Admin users can see all threads
        if user.has_role('admin'):
            return MessageThread.objects.all()

        # Users can see threads where they are a participant
        return MessageThread.objects.filter(participants__user=user, participants__is_active=True)

    def perform_create(self, serializer):
        """Set the creator to the current user when creating a thread"""
        thread = serializer.save(creator=self.request.user)

        # Add creator as a participant if not already added
        if not thread.participants.filter(user=self.request.user).exists():
            ThreadParticipant.objects.create(
                thread=thread,
                user=self.request.user,
                is_active=True
            )


class MessageThreadDetailView(generics.RetrieveAPIView):
    """
    Retrieve a message thread.
    """
    queryset = MessageThread.objects.all()
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]


class MessageThreadEditView(generics.UpdateAPIView):
    """
    Update a message thread.
    """
    queryset = MessageThread.objects.all()
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]


class MessageThreadDeleteView(generics.DestroyAPIView):
    """
    Delete a message thread.
    """
    queryset = MessageThread.objects.all()
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class ThreadParticipantListView(generics.ListCreateAPIView):
    """
    List all participants in a thread or add a new participant.
    """
    serializer_class = ThreadParticipantSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get participants for the specified thread"""
        thread_id = self.kwargs.get('thread_id')
        return ThreadParticipant.objects.filter(thread_id=thread_id)

    def perform_create(self, serializer):
        """Set the thread when creating a participant"""
        thread = get_object_or_404(MessageThread, id=self.kwargs.get('thread_id'))

        # Check if user has permission to add participants
        if not self.request.user.has_role('admin'):
            # Check if user is the creator of the thread
            if thread.creator != self.request.user:
                self.permission_denied(
                    self.request,
                    message=_('Only the thread creator or an admin can add participants.')
                )

        serializer.save(thread=thread)


class ThreadParticipantDetailView(generics.RetrieveAPIView):
    """
    Retrieve a thread participant.
    """
    queryset = ThreadParticipant.objects.all()
    serializer_class = ThreadParticipantSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]


class ThreadParticipantEditView(generics.UpdateAPIView):
    """
    Update a thread participant.
    """
    queryset = ThreadParticipant.objects.all()
    serializer_class = ThreadParticipantSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class ThreadParticipantDeleteView(generics.DestroyAPIView):
    """
    Delete a thread participant.
    """
    queryset = ThreadParticipant.objects.all()
    serializer_class = ThreadParticipantSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class MessageListCreateView(generics.ListCreateAPIView):
    """
    List all messages in a thread or create a new message.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['message_type', 'status', 'is_system_message', 'is_important']
    ordering_fields = ['sent_at']
    ordering = ['sent_at']

    def get_queryset(self):
        """Get messages for the specified thread"""
        thread_id = self.kwargs.get('thread_id')
        thread = get_object_or_404(MessageThread, id=thread_id)

        # Mark the thread as read for this user
        participant = thread.participants.filter(user=self.request.user, is_active=True).first()
        if participant:
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_at'])

        return Message.objects.filter(thread_id=thread_id)

    def perform_create(self, serializer):
        """Set the thread and sender when creating a message"""
        thread = get_object_or_404(MessageThread, id=self.kwargs.get('thread_id'))

        # Check if the thread is active
        if thread.status != 'active':
            self.permission_denied(
                self.request,
                message=_('Messages can only be sent in active threads.')
            )

        # Set sender and thread
        serializer.save(
            thread=thread,
            sender=self.request.user,
            sent_at=timezone.now()
        )


class MessageDetailView(generics.RetrieveAPIView):
    """
    Retrieve a message.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to mark message as read"""
        instance = self.get_object()

        # Mark as read if not already read
        if instance.sender != request.user and instance.status != 'read':
            instance.status = 'read'
            instance.read_at = timezone.now()
            instance.save(update_fields=['status', 'read_at'])

        return super().retrieve(request, *args, **kwargs)


class MessageEditView(generics.UpdateAPIView):
    """
    Update a message.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class MessageDeleteView(generics.DestroyAPIView):
    """
    Delete a message.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


# -------------------------------------------------------------------------
# Notification Views
# -------------------------------------------------------------------------

class NotificationListView(generics.ListAPIView):
    """
    List all notifications for the current user.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'is_read', 'is_sent', 'is_important']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get notifications for the current user"""
        return Notification.objects.filter(recipient=self.request.user)


class NotificationDetailView(generics.RetrieveAPIView):
    """
    Retrieve a notification.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only allow access to own notifications"""
        return Notification.objects.filter(recipient=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to mark notification as read"""
        instance = self.get_object()

        # Mark as read if not already read
        if not instance.is_read:
            instance.is_read = True
            instance.read_at = timezone.now()
            instance.save(update_fields=['is_read', 'read_at'])

        return super().retrieve(request, *args, **kwargs)


class NotificationEditView(generics.UpdateAPIView):
    """
    Update a notification.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only allow access to own notifications"""
        return Notification.objects.filter(recipient=self.request.user)


class NotificationDeleteView(generics.DestroyAPIView):
    """
    Delete a notification.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only allow access to own notifications"""
        return Notification.objects.filter(recipient=self.request.user)


# -------------------------------------------------------------------------
# Property View Views
# -------------------------------------------------------------------------

class PropertyViewListCreateView(generics.ListCreateAPIView):
    """
    List all property views for an auction or create a new property view.
    """
    serializer_class = PropertyViewSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['view_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get property views for the specified auction"""
        auction_id = self.kwargs.get('auction_id')
        return PropertyView.objects.filter(auction_id=auction_id)

    def perform_create(self, serializer):
        """Set the auction when creating a property view"""
        auction = get_object_or_404(Auction, id=self.kwargs.get('auction_id'))

        # Check if user has permission to add property views
        if not (self.request.user.has_role('admin') or auction.related_property.owner == self.request.user):
            self.permission_denied(
                self.request,
                message=_('You do not have permission to add property views to this auction.')
            )

        serializer.save(auction=auction)


class PropertyViewDetailView(generics.RetrieveAPIView):
    """
    Retrieve a property view.
    """
    queryset = PropertyView.objects.all()
    serializer_class = PropertyViewSerializer
    permission_classes = [IsAuthenticated]


class PropertyViewEditView(generics.UpdateAPIView):
    """
    Update a property view.
    """
    queryset = PropertyView.objects.all()
    serializer_class = PropertyViewSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def update(self, request, *args, **kwargs):
        """Check if user has permission to update this property view"""
        property_view = self.get_object()
        auction = property_view.auction

        if not (request.user.has_role('admin') or auction.related_property.owner == request.user):
            return Response(
                {'detail': _('You do not have permission to update this property view.')},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)


class PropertyViewDeleteView(generics.DestroyAPIView):
    """
    Delete a property view.
    """
    queryset = PropertyView.objects.all()
    serializer_class = PropertyViewSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        """Check if user has permission to delete this property view"""
        property_view = self.get_object()
        auction = property_view.auction

        if not (request.user.has_role('admin') or auction.related_property.owner == request.user):
            return Response(
                {'detail': _('You do not have permission to delete this property view.')},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().destroy(request, *args, **kwargs)
