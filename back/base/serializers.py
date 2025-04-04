from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Max
import json
from datetime import timedelta

from .models import (
    Property, Auction, Bid, Document, Contract, Payment, Transaction,
    PropertyView, MessageThread, Message, ThreadParticipant, Notification
)
from accounts.models import CustomUser, Role
from accounts.serializers import RoleSerializer, UserProfileSerializer

class JsonFieldMixin:
    """
    Mixin to handle JSON fields stored as text for SQLite compatibility.
    Provides methods to parse JSON fields and handle empty values.
    """
    def get_json_field(self, obj, field_name, default=None):
        """Helper method to get a JSON field value from model"""
        value = getattr(obj, field_name, None)
        if not value:
            return default if default is not None else ([] if field_name in ['images', 'videos', 'files', 'attachments'] else {})
            
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default if default is not None else ([] if field_name in ['images', 'videos', 'files', 'attachments'] else {})


# Property Serializers
class PropertyListSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Serializer for listing properties with essential information.
    Used for property listings with minimal details.
    """
    owner_name = serializers.SerializerMethodField()
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    main_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'property_number', 'title', 'slug', 'property_type', 'property_type_display',
            'status', 'status_display', 'city', 'district', 'area', 'estimated_value',
            'bedrooms', 'bathrooms', 'is_featured', 'is_published', 'views_count',
            'owner', 'owner_name', 'created_at', 'updated_at', 'main_image_url'
        ]
    
    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.email
    
    def get_main_image_url(self, obj):
        return obj.main_image_url


class PropertyDetailSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Detailed property serializer with all property information.
    Used for property detail views.
    """
    owner_details = UserProfileSerializer(source='owner', read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    facing_direction_display = serializers.CharField(source='get_facing_direction_display', read_only=True)
    current_usage_display = serializers.CharField(source='get_current_usage_display', read_only=True)
    optimal_usage_display = serializers.CharField(source='get_optimal_usage_display', read_only=True)
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    street_details = serializers.SerializerMethodField()
    rooms = serializers.SerializerMethodField()
    outdoor_spaces = serializers.SerializerMethodField()
    rental_details = serializers.SerializerMethodField()
    parking = serializers.SerializerMethodField()
    building_services = serializers.SerializerMethodField()
    infrastructure = serializers.SerializerMethodField()
    surroundings = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    reference_ids = serializers.SerializerMethodField()
    has_auction = serializers.BooleanField(read_only=True)
    location_coordinates = serializers.SerializerMethodField()
    active_auction_id = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = [
            'property_number', 'slug', 'views_count', 'verified_by', 
            'verification_date', 'is_verified', 'status_history',
            'has_auction', 'publish_date', 'created_at', 'updated_at'
        ]
    
    def get_images(self, obj):
        return self.get_json_field(obj, 'images', [])
    
    def get_videos(self, obj):
        return self.get_json_field(obj, 'videos', [])
    
    def get_features(self, obj):
        return self.get_json_field(obj, 'features', [])
    
    def get_amenities(self, obj):
        return self.get_json_field(obj, 'amenities', [])
    
    def get_street_details(self, obj):
        return self.get_json_field(obj, 'street_details', {})
    
    def get_rooms(self, obj):
        return self.get_json_field(obj, 'rooms', {})
    
    def get_outdoor_spaces(self, obj):
        return self.get_json_field(obj, 'outdoor_spaces', {})
    
    def get_rental_details(self, obj):
        return self.get_json_field(obj, 'rental_details', {})
    
    def get_parking(self, obj):
        return self.get_json_field(obj, 'parking', {})
    
    def get_building_services(self, obj):
        return self.get_json_field(obj, 'building_services', {})
    
    def get_infrastructure(self, obj):
        return self.get_json_field(obj, 'infrastructure', {})
    
    def get_surroundings(self, obj):
        return self.get_json_field(obj, 'surroundings', {})
    
    def get_location(self, obj):
        return self.get_json_field(obj, 'location', {})
    
    def get_reference_ids(self, obj):
        return self.get_json_field(obj, 'reference_ids', [])
    
    def get_location_coordinates(self, obj):
        return obj.location_coordinates
    
    def get_active_auction_id(self, obj):
        active_auction = obj.auctions.filter(status__in=['active', 'pending']).first()
        return active_auction.id if active_auction else None
    
    def get_documents_count(self, obj):
        return obj.property_documents.count()


class PropertySerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Base property serializer for create and update operations.
    Handles JSON serialization for SQLite compatibility.
    """
    images = serializers.JSONField(required=False)
    videos = serializers.JSONField(required=False)
    features = serializers.JSONField(required=False)
    amenities = serializers.JSONField(required=False)
    location = serializers.JSONField(required=False)
    street_details = serializers.JSONField(required=False)
    rooms = serializers.JSONField(required=False)
    outdoor_spaces = serializers.JSONField(required=False)
    rental_details = serializers.JSONField(required=False)
    parking = serializers.JSONField(required=False)
    building_services = serializers.JSONField(required=False)
    infrastructure = serializers.JSONField(required=False)
    surroundings = serializers.JSONField(required=False)
    reference_ids = serializers.JSONField(required=False)
    
    class Meta:
        model = Property
        exclude = ['property_number', 'slug', 'status_history', 'verification_details']
        read_only_fields = [
            'views_count', 'created_at', 'updated_at', 'verification_date',
            'publish_date', 'verified_by', 'is_verified'
        ]
    
    def to_internal_value(self, data):
        """Convert JSON fields to string for models using TextField for JSON"""
        # Process JSON fields that need to be stored as string in TextField
        json_fields = [
            'images', 'videos', 'features', 'amenities', 'location', 
            'street_details', 'rooms', 'outdoor_spaces', 'rental_details',
            'parking', 'building_services', 'infrastructure', 'surroundings', 
            'reference_ids'
        ]
        
        # Make a mutable copy if we have an immutable QueryDict
        if hasattr(data, '_mutable'):
            data = data.copy()
        
        # Convert JSON fields to string if they're dictionaries or lists
        for field in json_fields:
            if field in data and data[field]:
                if isinstance(data[field], (dict, list)):
                    data[field] = json.dumps(data[field])
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Custom validation for property data"""
        # Ensure area is positive
        if 'area' in data and data['area'] <= 0:
            raise serializers.ValidationError(_("Area must be greater than zero"))
        
        # Ensure estimated_value is positive
        if 'estimated_value' in data and data['estimated_value'] <= 0:
            raise serializers.ValidationError(_("Estimated value must be greater than zero"))
        
        # Validate status transition if updating
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status,
                    data['status'],
                    self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})
        
        return data


# Auction Serializers
class AuctionListSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Serializer for listing auctions with essential information.
    Used for auction listings with minimal details.
    """
    property_title = serializers.CharField(source='related_property.title', read_only=True)
    property_type = serializers.CharField(source='related_property.property_type', read_only=True)
    property_city = serializers.CharField(source='related_property.city', read_only=True)
    auction_type_display = serializers.CharField(source='get_auction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    bid_count = serializers.IntegerField(read_only=True)
    highest_bid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    time_remaining = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    featured_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Auction
        fields = [
            'id', 'uuid', 'title', 'slug', 'auction_type', 'auction_type_display',
            'status', 'status_display', 'start_date', 'end_date', 'starting_price',
            'current_bid', 'bid_count', 'highest_bid', 'reserve_price', 'is_featured',
            'is_published', 'views_count', 'is_private', 'related_property', 'property_title',
            'property_type', 'property_city', 'time_remaining', 'is_active', 'featured_image_url',
            'created_at', 'auctioneer'
        ]
    
    def get_featured_image_url(self, obj):
        return obj.featured_image_url


class AuctionDetailSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Detailed auction serializer with all auction information.
    Used for auction detail views.
    """
    property_details = PropertyListSerializer(source='related_property', read_only=True)
    created_by_details = UserProfileSerializer(source='created_by', read_only=True)
    auctioneer_details = UserProfileSerializer(source='auctioneer', read_only=True)
    winning_bidder_details = UserProfileSerializer(source='winning_bidder', read_only=True)
    auction_type_display = serializers.CharField(source='get_auction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    bid_count = serializers.IntegerField(read_only=True)
    unique_bidders_count = serializers.IntegerField(read_only=True)
    highest_bid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    time_remaining = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    location_coordinates = serializers.SerializerMethodField()
    invited_bidders_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = '__all__'
        read_only_fields = [
            'uuid', 'slug', 'views_count', 'current_bid', 'winning_bid',
            'winning_bidder', 'publish_date', 'created_at', 'updated_at'
        ]
    
    def get_images(self, obj):
        return self.get_json_field(obj, 'images', [])
    
    def get_videos(self, obj):
        return self.get_json_field(obj, 'videos', [])
    
    def get_documents(self, obj):
        return self.get_json_field(obj, 'documents', [])
    
    def get_location(self, obj):
        return self.get_json_field(obj, 'location', {})
    
    def get_location_coordinates(self, obj):
        return obj.location_coordinates
    
    def get_invited_bidders_count(self, obj):
        return obj.invited_bidders.count()
    
    def get_documents_count(self, obj):
        return obj.auction_documents.count()


class AuctionSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Base auction serializer for create and update operations.
    Handles JSON serialization for SQLite compatibility.
    """
    images = serializers.JSONField(required=False)
    videos = serializers.JSONField(required=False)
    documents = serializers.JSONField(required=False)
    location = serializers.JSONField(required=False)

    class Meta:
        model = Auction
        exclude = ['uuid', 'slug']
        read_only_fields = [
            'views_count', 'current_bid', 'winning_bid', 'winning_bidder',
            'publish_date', 'created_at', 'updated_at'
        ]
    
    def to_internal_value(self, data):
        """Convert JSON fields to string for models using TextField for JSON"""
        json_fields = ['images', 'videos', 'documents', 'location']
        
        # Make a mutable copy if we have an immutable QueryDict
        if hasattr(data, '_mutable'):
            data = data.copy()
        
        # Convert JSON fields to string if they're dictionaries or lists
        for field in json_fields:
            if field in data and data[field]:
                if isinstance(data[field], (dict, list)):
                    data[field] = json.dumps(data[field])
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Custom validation for auction data"""
        # Ensure start_date is in the future for new auctions
        if not self.instance and 'start_date' in data:
            if data['start_date'] <= timezone.now():
                raise serializers.ValidationError({"start_date": _("Start date must be in the future")})
        
        # Ensure end_date is after start_date
        if 'start_date' in data and 'end_date' in data:
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError({"end_date": _("End date must be after start date")})
        elif 'end_date' in data and self.instance:
            if data['end_date'] <= self.instance.start_date:
                raise serializers.ValidationError({"end_date": _("End date must be after start date")})
        elif 'start_date' in data and self.instance:
            if self.instance.end_date <= data['start_date']:
                raise serializers.ValidationError({"start_date": _("Start date must be before end date")})
        
        # Validate status transition if updating
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status,
                    data['status'],
                    self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})
        
        # Ensure starting_price is positive
        if 'starting_price' in data and data['starting_price'] <= 0:
            raise serializers.ValidationError({"starting_price": _("Starting price must be greater than zero")})
        
        # Ensure reserve_price is greater than or equal to starting_price
        if 'reserve_price' in data and 'starting_price' in data:
            if data['reserve_price'] < data['starting_price']:
                raise serializers.ValidationError({"reserve_price": _("Reserve price must be greater than or equal to starting price")})
        
        return data


# Bid Serializers
class BidListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing bids with essential information.
    Used for bid listings with minimal details.
    """
    bidder_name = serializers.SerializerMethodField()
    auction_title = serializers.CharField(source='auction.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id', 'auction', 'auction_title', 'bidder', 'bidder_name',
            'bid_amount', 'bid_time', 'status', 'status_display',
            'is_auto_bid', 'created_at', 'updated_at'
        ]
    
    def get_bidder_name(self, obj):
        return obj.bidder.get_full_name() or obj.bidder.email


class BidDetailSerializer(serializers.ModelSerializer):
    """
    Detailed bid serializer with all bid information.
    Used for bid detail views.
    """
    bidder_details = UserProfileSerializer(source='bidder', read_only=True)
    auction_details = AuctionListSerializer(source='auction', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    device_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Bid
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'bid_time', 'ip_address', 'user_agent']
    
    def get_device_info(self, obj):
        try:
            if obj.device_info:
                return json.loads(obj.device_info)
        except (json.JSONDecodeError, TypeError):
            pass
        return {}


class BidSerializer(serializers.ModelSerializer):
    """
    Base bid serializer for create and update operations.
    """
    class Meta:
        model = Bid
        fields = [
            'auction', 'bidder', 'bid_amount', 'status', 
            'max_bid_amount', 'is_auto_bid', 'notes'
        ]
    
    def validate(self, data):
        """Custom validation for bid data"""
        # Ensure bid_amount is positive
        if 'bid_amount' in data and data['bid_amount'] <= 0:
            raise serializers.ValidationError({"bid_amount": _("Bid amount must be greater than zero")})
        
        # If creating a new bid
        if not self.instance:
            auction = data.get('auction')
            if auction:
                # Check auction status
                if auction.status != 'active':
                    raise serializers.ValidationError(_("Cannot place bid on an inactive auction"))
                
                # Check auction timing
                now = timezone.now()
                if now < auction.start_date:
                    raise serializers.ValidationError(_("The auction hasn't started yet"))
                if now > auction.end_date:
                    raise serializers.ValidationError(_("The auction has already ended"))
                
                # Validate bid amount
                highest_bid = auction.highest_bid
                min_bid = highest_bid + auction.min_bid_increment
                
                if data.get('bid_amount', 0) < min_bid:
                    raise serializers.ValidationError({
                        "bid_amount": _("Bid amount must be at least {}").format(min_bid)
                    })
        
        return data
    
    def to_internal_value(self, data):
        """Convert device_info JSON to string for models using TextField for JSON"""
        if 'device_info' in data and data['device_info']:
            if isinstance(data['device_info'], dict):
                data = data.copy() if hasattr(data, '_mutable') else data
                data['device_info'] = json.dumps(data['device_info'])
        
        return super().to_internal_value(data)


# Document Serializers
class DocumentListSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Serializer for listing documents with essential information.
    Used for document listings with minimal details.
    """
    uploaded_by_name = serializers.SerializerMethodField()
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    files_count = serializers.SerializerMethodField()
    main_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'document_number', 'title', 'document_type', 'document_type_display',
            'verification_status', 'verification_status_display', 'uploaded_by',
            'uploaded_by_name', 'related_property', 'auction', 'contract',
            'issue_date', 'expiry_date', 'created_at', 'updated_at',
            'files_count', 'main_file_url'
        ]
    
    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.email
        return None
    
    def get_files_count(self, obj):
        files = self.get_json_field(obj, 'files', [])
        return len(files)
    
    def get_main_file_url(self, obj):
        return obj.main_file_url


class DocumentDetailSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Detailed document serializer with all document information.
    Used for document detail views.
    """
    uploaded_by_details = UserProfileSerializer(source='uploaded_by', read_only=True)
    verified_by_details = UserProfileSerializer(source='verified_by', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    files = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    property_title = serializers.SerializerMethodField()
    auction_title = serializers.SerializerMethodField()
    contract_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = [
            'document_number', 'verification_date', 'verified_by',
            'created_at', 'updated_at'
        ]
    
    def get_files(self, obj):
        return self.get_json_field(obj, 'files', [])
    
    def get_metadata(self, obj):
        return self.get_json_field(obj, 'metadata', {})
    
    def get_property_title(self, obj):
        if obj.related_property:
            return obj.related_property.title
        return None
    
    def get_auction_title(self, obj):
        if obj.auction:
            return obj.auction.title
        return None
    
    def get_contract_title(self, obj):
        if obj.contract:
            return obj.contract.title
        return None


class DocumentSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Base document serializer for create and update operations.
    Handles JSON serialization for SQLite compatibility.
    """
    files = serializers.JSONField(required=False)
    metadata = serializers.JSONField(required=False)
    
    class Meta:
        model = Document
        exclude = ['document_number']
        read_only_fields = [
            'verification_date', 'verified_by', 'created_at', 'updated_at'
        ]
    
    def to_internal_value(self, data):
        """Convert JSON fields to string for models using TextField for JSON"""
        json_fields = ['files', 'metadata']
        
        # Make a mutable copy if we have an immutable QueryDict
        if hasattr(data, '_mutable'):
            data = data.copy()
        
        # Convert JSON fields to string if they're dictionaries or lists
        for field in json_fields:
            if field in data and data[field]:
                if isinstance(data[field], (dict, list)):
                    data[field] = json.dumps(data[field])
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Custom validation for document data"""
        # Ensure at least one related entity
        if not data.get('related_property') and not data.get('auction') and not data.get('contract'):
            raise serializers.ValidationError(_("Document must be related to a property, auction, or contract"))
        
        # Validate verification status transition if updating
        if self.instance and 'verification_status' in data and data['verification_status'] != self.instance.verification_status:
            try:
                self.instance.validate_status_transition(
                    self.instance.verification_status,
                    data['verification_status'],
                    self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"verification_status": str(e)})
        
        # Validate expiry date is after issue date
        if 'issue_date' in data and 'expiry_date' in data and data['expiry_date'] and data['issue_date']:
            if data['expiry_date'] <= data['issue_date']:
                raise serializers.ValidationError({"expiry_date": _("Expiry date must be after issue date")})
        
        return data


# Contract Serializers
class ContractListSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Serializer for listing contracts with essential information.
    Used for contract listings with minimal details.
    """
    property_title = serializers.CharField(source='related_property.title', read_only=True)
    auction_title = serializers.CharField(source='auction.title', read_only=True)
    buyer_name = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    signing_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'title', 'status', 'status_display',
            'contract_date', 'effective_date', 'expiry_date', 'contract_amount',
            'total_amount', 'payment_method', 'payment_method_display',
            'related_property', 'property_title', 'auction', 'auction_title',
            'buyer', 'buyer_name', 'seller', 'seller_name', 'agent',
            'buyer_signed', 'seller_signed', 'agent_signed', 'signing_status',
            'created_at', 'updated_at'
        ]
    
    def get_buyer_name(self, obj):
        return obj.buyer.get_full_name() or obj.buyer.email
    
    def get_seller_name(self, obj):
        return obj.seller.get_full_name() or obj.seller.email
    
    def get_signing_status(self, obj):
        """Get contract signing status"""
        if obj.buyer_signed and obj.seller_signed and (not obj.agent or obj.agent_signed):
            return "fully_signed"
        elif obj.buyer_signed or obj.seller_signed or obj.agent_signed:
            return "partially_signed"
        else:
            return "unsigned"


class ContractDetailSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Detailed contract serializer with all contract information.
    Used for contract detail views.
    """
    property_details = PropertyListSerializer(source='related_property', read_only=True)
    auction_details = AuctionListSerializer(source='auction', read_only=True)
    buyer_details = UserProfileSerializer(source='buyer', read_only=True)
    seller_details = UserProfileSerializer(source='seller', read_only=True)
    agent_details = UserProfileSerializer(source='agent', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    files = serializers.SerializerMethodField()
    is_fully_signed = serializers.BooleanField(read_only=True)
    payments_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    payments_total = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = '__all__'
        read_only_fields = [
            'contract_number', 'buyer_signed', 'seller_signed', 'agent_signed',
            'buyer_signature_date', 'seller_signature_date', 'agent_signature_date',
            'is_verified', 'verification_authority', 'verification_date',
            'created_at', 'updated_at'
        ]
    
    def get_files(self, obj):
        return self.get_json_field(obj, 'files', [])
    
    def get_payments_count(self, obj):
        return obj.payments.count()
    
    def get_documents_count(self, obj):
        return obj.contract_documents.count()
    
    def get_payments_total(self, obj):
        completed_payments = obj.payments.filter(status='completed')
        total = completed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
        return total
    
    def get_remaining_amount(self, obj):
        completed_payments = obj.payments.filter(status='completed')
        total_paid = completed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
        return obj.total_amount - total_paid


class ContractSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Base contract serializer for create and update operations.
    Handles JSON serialization for SQLite compatibility.
    """
    files = serializers.JSONField(required=False)
    
    class Meta:
        model = Contract
        exclude = ['contract_number']
        read_only_fields = [
            'buyer_signed', 'seller_signed', 'agent_signed',
            'buyer_signature_date', 'seller_signature_date', 'agent_signature_date',
            'is_verified', 'verification_authority', 'verification_date',
            'created_at', 'updated_at'
        ]
    
    def to_internal_value(self, data):
        """Convert JSON fields to string for models using TextField for JSON"""
        if 'files' in data and data['files']:
            if isinstance(data['files'], (dict, list)):
                data = data.copy() if hasattr(data, '_mutable') else data
                data['files'] = json.dumps(data['files'])
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Custom validation for contract data"""
        # Ensure contract_amount is positive
        if 'contract_amount' in data and data['contract_amount'] <= 0:
            raise serializers.ValidationError({"contract_amount": _("Contract amount must be greater than zero")})
        
        # Validate total_amount is greater than or equal to contract_amount
        if 'total_amount' in data and 'contract_amount' in data:
            if data['total_amount'] < data['contract_amount']:
                raise serializers.ValidationError({
                    "total_amount": _("Total amount must be greater than or equal to contract amount")
                })
        
        # Validate property matches auction property
        if 'auction' in data and 'related_property' in data:
            if data['auction'].related_property.id != data['related_property'].id:
                raise serializers.ValidationError(_("Property must match the auction's property"))
        
        # Validate status transition if updating
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status,
                    data['status'],
                    self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})
        
        # Validate effective date is on or after contract date
        if 'contract_date' in data and 'effective_date' in data and data['effective_date']:
            if data['effective_date'] < data['contract_date']:
                raise serializers.ValidationError({
                    "effective_date": _("Effective date must be on or after contract date")
                })
        
        # Validate expiry date is after effective date
        if 'effective_date' in data and 'expiry_date' in data and data['expiry_date'] and data['effective_date']:
            if data['expiry_date'] <= data['effective_date']:
                raise serializers.ValidationError({
                    "expiry_date": _("Expiry date must be after effective date")
                })
        
        return data


# Payment Serializers
class PaymentListSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Serializer for listing payments with essential information.
    Used for payment listings with minimal details.
    """
    payer_name = serializers.SerializerMethodField()
    payee_name = serializers.SerializerMethodField()
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'payment_type', 'payment_type_display',
            'payment_method', 'payment_method_display', 'amount', 'currency',
            'payment_date', 'due_date', 'status', 'status_display',
            'contract', 'contract_number', 'payer', 'payer_name',
            'payee', 'payee_name', 'confirmed_at', 'is_overdue',
            'created_at', 'updated_at'
        ]
    
    def get_payer_name(self, obj):
        return obj.payer.get_full_name() or obj.payer.email
    
    def get_payee_name(self, obj):
        return obj.payee.get_full_name() or obj.payee.email


class PaymentDetailSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Detailed payment serializer with all payment information.
    Used for payment detail views.
    """
    payer_details = UserProfileSerializer(source='payer', read_only=True)
    payee_details = UserProfileSerializer(source='payee', read_only=True)
    confirmed_by_details = UserProfileSerializer(source='confirmed_by', read_only=True)
    contract_details = ContractListSerializer(source='contract', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    files = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    receipt_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = [
            'payment_number', 'confirmed_at', 'confirmed_by',
            'created_at', 'updated_at'
        ]
    
    def get_files(self, obj):
        return self.get_json_field(obj, 'files', [])
    
    def get_receipt_url(self, obj):
        return obj.receipt_url
    
    def get_transactions(self, obj):
        """Get basic transaction info for this payment"""
        transactions = obj.transactions.all()
        return [{
            'id': t.id,
            'transaction_number': t.transaction_number,
            'transaction_type': t.transaction_type,
            'amount': t.amount,
            'status': t.status,
            'transaction_date': t.transaction_date
        } for t in transactions]


class PaymentSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Base payment serializer for create and update operations.
    Handles JSON serialization for SQLite compatibility.
    """
    files = serializers.JSONField(required=False)
    
    class Meta:
        model = Payment
        exclude = ['payment_number']
        read_only_fields = [
            'confirmed_at', 'confirmed_by', 'created_at', 'updated_at'
        ]
    
    def to_internal_value(self, data):
        """Convert JSON fields to string for models using TextField for JSON"""
        if 'files' in data and data['files']:
            if isinstance(data['files'], (dict, list)):
                data = data.copy() if hasattr(data, '_mutable') else data
                data['files'] = json.dumps(data['files'])
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Custom validation for payment data"""
        # Ensure amount is positive
        if 'amount' in data and data['amount'] <= 0:
            raise serializers.ValidationError({"amount": _("Amount must be greater than zero")})
        
        # Validate payment_date is not in the future for new payments
        if not self.instance and 'payment_date' in data:
            if data['payment_date'] > timezone.now() + timedelta(minutes=5):  # Allow 5 min buffer
                raise serializers.ValidationError({
                    "payment_date": _("Payment date cannot be in the future")
                })
        
        # Validate due date is after payment date
        if 'payment_date' in data and 'due_date' in data and data['due_date']:
            payment_date = data['payment_date'].date() if hasattr(data['payment_date'], 'date') else data['payment_date']
            if data['due_date'] < payment_date:
                raise serializers.ValidationError({
                    "due_date": _("Due date must be on or after payment date")
                })
        
        # Validate status transition if updating
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status,
                    data['status'],
                    self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})
        
        # For certain payment types, validate payer/payee match contract roles
        if 'payment_type' in data and 'contract' in data:
            payment_type = data['payment_type']
            contract = data['contract']
            
            if payment_type in ['deposit', 'full_payment', 'installment']:
                if 'payer' in data and data['payer'] != contract.buyer:
                    raise serializers.ValidationError({
                        "payer": _("For {} payments, the payer must be the buyer").format(payment_type)
                    })
                
                if 'payee' in data and data['payee'] != contract.seller:
                    raise serializers.ValidationError({
                        "payee": _("For {} payments, the payee must be the seller").format(payment_type)
                    })
        
        return data


# Transaction Serializers
class TransactionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing transactions with essential information.
    Used for transaction listings with minimal details.
    """
    from_user_name = serializers.SerializerMethodField()
    to_user_name = serializers.SerializerMethodField()
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_number', 'transaction_type', 'transaction_type_display',
            'amount', 'currency', 'status', 'status_display', 'transaction_date',
            'from_user', 'from_user_name', 'to_user', 'to_user_name',
            'payment', 'auction', 'contract', 'reference',
            'processed_at', 'created_at', 'updated_at'
        ]
    
    def get_from_user_name(self, obj):
        return obj.from_user.get_full_name() or obj.from_user.email
    
    def get_to_user_name(self, obj):
        return obj.to_user.get_full_name() or obj.to_user.email


class TransactionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed transaction serializer with all transaction information.
    Used for transaction detail views.
    """
    from_user_details = UserProfileSerializer(source='from_user', read_only=True)
    to_user_details = UserProfileSerializer(source='to_user', read_only=True)
    processed_by_details = UserProfileSerializer(source='processed_by', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_details = PaymentListSerializer(source='payment', read_only=True)
    auction_details = serializers.SerializerMethodField()
    contract_details = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = [
            'transaction_number', 'processed_at', 'created_at', 'updated_at'
        ]
    
    def get_auction_details(self, obj):
        if obj.auction:
            return {
                'id': obj.auction.id,
                'title': obj.auction.title,
                'status': obj.auction.status
            }
        return None
    
    def get_contract_details(self, obj):
        if obj.contract:
            return {
                'id': obj.contract.id,
                'title': obj.contract.title,
                'contract_number': obj.contract.contract_number,
                'status': obj.contract.status
            }
        return None


class TransactionSerializer(serializers.ModelSerializer):
    """
    Base transaction serializer for create and update operations.
    """
    class Meta:
        model = Transaction
        exclude = ['transaction_number']
        read_only_fields = [
            'processed_at', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Custom validation for transaction data"""
        # Ensure amount is positive
        if 'amount' in data and data['amount'] <= 0:
            raise serializers.ValidationError({"amount": _("Amount must be greater than zero")})
        
        # Validate transaction_date is not in the future
        if 'transaction_date' in data:
            if data['transaction_date'] > timezone.now() + timedelta(minutes=5):  # Allow 5 min buffer
                raise serializers.ValidationError({
                    "transaction_date": _("Transaction date cannot be in the future")
                })
        
        # Ensure at least one related entity
        if not data.get('payment') and not data.get('auction') and not data.get('contract'):
            raise serializers.ValidationError(_("Transaction must be related to a payment, auction, or contract"))
        
        # Validate status transition if updating
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status,
                    data['status'],
                    self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})
        
        return data


# PropertyView Serializers
class PropertyViewListSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Serializer for listing property views with essential information.
    Used for property view listings with minimal details.
    """
    view_type_display = serializers.CharField(source='get_view_type_display', read_only=True)
    main_image_url = serializers.SerializerMethodField()
    auction_title = serializers.CharField(source='auction.title', read_only=True)
    property_title = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyView
        fields = [
            'id', 'auction', 'auction_title', 'view_type', 'view_type_display',
            'size_sqm', 'location', 'elevation', 'view_direction',
            'condition', 'main_image_url', 'property_title',
            'created_at', 'updated_at'
        ]
    
    def get_main_image_url(self, obj):
        return obj.main_image_url
    
    def get_property_title(self, obj):
        if obj.related_property:
            return obj.related_property.title
        return None


class PropertyViewDetailSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Detailed property view serializer with all property view information.
    Used for property view detail views.
    """
    view_type_display = serializers.CharField(source='get_view_type_display', read_only=True)
    images = serializers.SerializerMethodField()
    historical_views = serializers.SerializerMethodField()
    auction_details = AuctionListSerializer(source='auction', read_only=True)
    property_details = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    formatted_elevation = serializers.CharField(read_only=True)
    
    class Meta:
        model = PropertyView
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_images(self, obj):
        return self.get_json_field(obj, 'images', [])
    
    def get_historical_views(self, obj):
        return self.get_json_field(obj, 'historical_views', {})
    
    def get_main_image_url(self, obj):
        return obj.main_image_url
    
    def get_property_details(self, obj):
        if obj.related_property:
            return PropertyListSerializer(obj.related_property).data
        return None


class PropertyViewSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Base property view serializer for create and update operations.
    Handles JSON serialization for SQLite compatibility.
    """
    images = serializers.JSONField(required=False)
    historical_views = serializers.JSONField(required=False)
    
    class Meta:
        model = PropertyView
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def to_internal_value(self, data):
        """Convert JSON fields to string for models using TextField for JSON"""
        json_fields = ['images', 'historical_views']
        
        # Make a mutable copy if we have an immutable QueryDict
        if hasattr(data, '_mutable'):
            data = data.copy()
        
        # Convert JSON fields to string if they're dictionaries or lists
        for field in json_fields:
            if field in data and data[field]:
                if isinstance(data[field], (dict, list)):
                    data[field] = json.dumps(data[field])
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Custom validation for property view data"""
        # Ensure size_sqm is positive
        if 'size_sqm' in data and data['size_sqm'] <= 0:
            raise serializers.ValidationError({"size_sqm": _("Size must be greater than zero")})
        
        return data


# MessageThread Serializers
class MessageThreadListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing message threads with essential information.
    Used for message thread listings with minimal details.
    """
    creator_name = serializers.SerializerMethodField()
    thread_type_display = serializers.CharField(source='get_thread_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    participants_count = serializers.SerializerMethodField()
    unread_messages = serializers.SerializerMethodField()
    message_count = serializers.IntegerField(read_only=True)
    related_entity = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageThread
        fields = [
            'id', 'uuid', 'subject', 'thread_type', 'thread_type_display',
            'status', 'status_display', 'creator', 'creator_name',
            'is_private', 'is_system_thread', 'last_message_at',
            'participants_count', 'message_count', 'unread_messages',
            'related_property', 'related_auction', 'related_contract',
            'related_entity', 'created_at', 'updated_at'
        ]
    
    def get_creator_name(self, obj):
        if obj.creator:
            return obj.creator.get_full_name() or obj.creator.email
        return None
    
    def get_participants_count(self, obj):
        return obj.thread_participants.filter(is_active=True).count()
    
    def get_unread_messages(self, obj):
        """Get unread message count for current user"""
        user = self.context.get('user')
        if not user:
            return 0
        
        participant = obj.thread_participants.filter(user=user, is_active=True).first()
        if not participant:
            return 0
        
        return participant.unread_count
    
    def get_related_entity(self, obj):
        """Get details of the primary related entity"""
        if obj.related_property:
            return {
                'type': 'property',
                'id': obj.related_property.id,
                'title': obj.related_property.title
            }
        elif obj.related_auction:
            return {
                'type': 'auction',
                'id': obj.related_auction.id,
                'title': obj.related_auction.title
            }
        elif obj.related_contract:
            return {
                'type': 'contract',
                'id': obj.related_contract.id,
                'title': obj.related_contract.title,
                'contract_number': obj.related_contract.contract_number
            }
        return None


class MessageThreadDetailSerializer(serializers.ModelSerializer):
    """
    Detailed message thread serializer with all message thread information.
    Used for message thread detail views.
    """
    creator_details = UserProfileSerializer(source='creator', read_only=True)
    thread_type_display = serializers.CharField(source='get_thread_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    participants = serializers.SerializerMethodField()
    messages_count = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True)
    property_details = serializers.SerializerMethodField()
    auction_details = serializers.SerializerMethodField()
    contract_details = serializers.SerializerMethodField()
    user_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageThread
        fields = '__all__'
        read_only_fields = [
            'uuid', 'created_at', 'updated_at', 'last_message_at'
        ]
    
    def get_participants(self, obj):
        """Get basic info about active participants"""
        participants = obj.thread_participants.filter(is_active=True)
        return [{
            'id': p.id,
            'user_id': p.user.id,
            'name': p.user.get_full_name() or p.user.email,
            'email': p.user.email,
            'role': p.role.name if p.role else 'member',
            'role_display': p.role.get_name_display() if p.role else _('Member'),
            'is_muted': p.is_muted,
            'last_read_at': p.last_read_at,
            'joined_at': p.created_at
        } for p in participants]
    
    def get_messages_count(self, obj):
        return obj.messages.count()
    
    def get_property_details(self, obj):
        if obj.related_property:
            return {
                'id': obj.related_property.id,
                'title': obj.related_property.title,
                'property_type': obj.related_property.property_type,
                'city': obj.related_property.city
            }
        return None
    
    def get_auction_details(self, obj):
        if obj.related_auction:
            return {
                'id': obj.related_auction.id,
                'title': obj.related_auction.title,
                'status': obj.related_auction.status,
                'auction_type': obj.related_auction.auction_type
            }
        return None
    
    def get_contract_details(self, obj):
        if obj.related_contract:
            return {
                'id': obj.related_contract.id,
                'title': obj.related_contract.title,
                'contract_number': obj.related_contract.contract_number,
                'status': obj.related_contract.status
            }
        return None
    
    def get_user_participant(self, obj):
        """Get current user's participation details"""
        user = self.context.get('user')
        if not user:
            return None
        
        participant = obj.thread_participants.filter(user=user, is_active=True).first()
        if not participant:
            return None
        
        return {
            'id': participant.id,
            'role': participant.role.name if participant.role else 'member',
            'role_display': participant.role.get_name_display() if participant.role else _('Member'),
            'is_muted': participant.is_muted,
            'last_read_at': participant.last_read_at,
            'has_unread_messages': participant.has_unread_messages,
            'unread_count': participant.unread_count
        }


class MessageThreadSerializer(serializers.ModelSerializer):
    """
    Base message thread serializer for create and update operations.
    """
    class Meta:
        model = MessageThread
        exclude = ['uuid']
        read_only_fields = [
            'last_message_at', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Custom validation for message thread data"""
        # Ensure only one status is active
        if 'status' in data and data['status'] not in ['active', 'closed', 'archived', 'deleted']:
            raise serializers.ValidationError({"status": _("Invalid status value")})
        
        return data


# Message Serializers
class MessageListSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Serializer for listing messages with essential information.
    Used for message listings with minimal details.
    """
    sender_name = serializers.SerializerMethodField()
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_attachments = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'thread', 'sender', 'sender_name', 'subject',
            'content', 'message_type', 'message_type_display',
            'status', 'status_display', 'sent_at', 'delivered_at',
            'read_at', 'is_system_message', 'is_important',
            'has_attachments', 'parent_message', 'created_at'
        ]
    
    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.email


class MessageDetailSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Detailed message serializer with all message information.
    Used for message detail views.
    """
    sender_details = UserProfileSerializer(source='sender', read_only=True)
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    attachments = serializers.SerializerMethodField()
    parent_message_details = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    property_details = serializers.SerializerMethodField()
    auction_details = serializers.SerializerMethodField()
    contract_details = serializers.SerializerMethodField()
    thread_subject = serializers.CharField(source='thread.subject', read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = [
            'sent_at', 'delivered_at', 'read_at', 'created_at', 'updated_at'
        ]
    
    def get_attachments(self, obj):
        return self.get_json_field(obj, 'attachments', [])
    
    def get_parent_message_details(self, obj):
        if obj.parent_message:
            return {
                'id': obj.parent_message.id,
                'sender': obj.parent_message.sender.get_full_name() or obj.parent_message.sender.email,
                'content': obj.parent_message.content[:100] + ('...' if len(obj.parent_message.content) > 100 else ''),
                'sent_at': obj.parent_message.sent_at
            }
        return None
    
    def get_replies_count(self, obj):
        return obj.replies.count()
    
    def get_property_details(self, obj):
        if obj.related_property:
            return {
                'id': obj.related_property.id,
                'title': obj.related_property.title
            }
        return None
    
    def get_auction_details(self, obj):
        if obj.related_auction:
            return {
                'id': obj.related_auction.id,
                'title': obj.related_auction.title
            }
        return None
    
    def get_contract_details(self, obj):
        if obj.related_contract:
            return {
                'id': obj.related_contract.id,
                'title': obj.related_contract.title,
                'contract_number': obj.related_contract.contract_number
            }
        return None


class MessageSerializer(JsonFieldMixin, serializers.ModelSerializer):
    """
    Base message serializer for create and update operations.
    Handles JSON serialization for SQLite compatibility.
    """
    attachments = serializers.JSONField(required=False)
    
    class Meta:
        model = Message
        fields = [
            'thread', 'sender', 'subject', 'content', 'message_type',
            'status', 'parent_message', 'attachments', 'is_system_message',
            'is_important', 'related_property', 'related_auction', 'related_contract'
        ]
        read_only_fields = [
            'sent_at', 'delivered_at', 'read_at'
        ]
    
    def to_internal_value(self, data):
        """Convert JSON fields to string for models using TextField for JSON"""
        if 'attachments' in data and data['attachments']:
            if isinstance(data['attachments'], (dict, list)):
                data = data.copy() if hasattr(data, '_mutable') else data
                data['attachments'] = json.dumps(data['attachments'])
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Custom validation for message data"""
        # Ensure content is not empty
        if 'content' in data and not data['content'].strip():
            raise serializers.ValidationError({"content": _("Content cannot be empty")})
        
        # Ensure sender is a participant in the thread
        if 'thread' in data and 'sender' in data:
            thread = data['thread']
            sender = data['sender']
            
            # Check if user is a participant
            is_participant = ThreadParticipant.objects.filter(
                thread=thread,
                user=sender,
                is_active=True
            ).exists()
            
            if not is_participant:
                raise serializers.ValidationError(_("Sender must be an active participant in the thread"))
        
        # Validate parent message belongs to the same thread
        if 'parent_message' in data and data['parent_message'] and 'thread' in data:
            if data['parent_message'].thread != data['thread']:
                raise serializers.ValidationError({
                    "parent_message": _("Parent message must belong to the same thread")
                })
        
        return data


# ThreadParticipant Serializers
class ThreadParticipantSerializer(serializers.ModelSerializer):
    """
    Basic thread participant serializer with essential information.
    """
    user_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ThreadParticipant
        fields = [
            'id', 'thread', 'user', 'user_name', 'role', 'role_name',
            'is_active', 'is_muted', 'last_read_at', 'created_at'
        ]
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email
    
    def get_role_name(self, obj):
        if obj.role:
            return obj.role.get_name_display()
        return _('Member')


class ThreadParticipantDetailSerializer(serializers.ModelSerializer):
    """
    Detailed thread participant serializer with all participant information.
    """
    user_details = UserProfileSerializer(source='user', read_only=True)
    role_details = RoleSerializer(source='role', read_only=True)
    custom_permissions = serializers.JSONField(read_only=True)
    has_unread_messages = serializers.BooleanField(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ThreadParticipant
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# Notification Serializers
class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing notifications with essential information.
    Used for notification listings with minimal details.
    """
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'notification_type', 'notification_type_display',
            'title', 'content', 'is_read', 'read_at', 'is_sent',
            'sent_at', 'is_actionable', 'icon', 'color', 'action_url',
            'related_property', 'related_auction', 'related_bid',
            'related_contract', 'related_payment', 'related_message',
            'created_at'
        ]


class NotificationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed notification serializer with all notification information.
    Used for notification detail views.
    """
    recipient_details = UserProfileSerializer(source='recipient', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    is_actionable = serializers.BooleanField(read_only=True)
    property_details = serializers.SerializerMethodField()
    auction_details = serializers.SerializerMethodField()
    bid_details = serializers.SerializerMethodField()
    contract_details = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()
    message_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'read_at', 'sent_at']
    
    def get_property_details(self, obj):
        if obj.related_property:
            return {
                'id': obj.related_property.id,
                'title': obj.related_property.title,
                'property_type': obj.related_property.property_type
            }
        return None
    
    def get_auction_details(self, obj):
        if obj.related_auction:
            return {
                'id': obj.related_auction.id,
                'title': obj.related_auction.title,
                'status': obj.related_auction.status
            }
        return None
    
    def get_bid_details(self, obj):
        if obj.related_bid:
            return {
                'id': obj.related_bid.id,
                'bid_amount': obj.related_bid.bid_amount,
                'bidder': obj.related_bid.bidder.get_full_name() or obj.related_bid.bidder.email,
                'bid_time': obj.related_bid.bid_time
            }
        return None
    
    def get_contract_details(self, obj):
        if obj.related_contract:
            return {
                'id': obj.related_contract.id,
                'title': obj.related_contract.title,
                'contract_number': obj.related_contract.contract_number,
                'status': obj.related_contract.status
            }
        return None
    
    def get_payment_details(self, obj):
        if obj.related_payment:
            return {
                'id': obj.related_payment.id,
                'payment_number': obj.related_payment.payment_number,
                'amount': obj.related_payment.amount,
                'payment_type': obj.related_payment.payment_type
            }
        return None
    
    def get_message_details(self, obj):
        if obj.related_message:
            return {
                'id': obj.related_message.id,
                'sender': obj.related_message.sender.get_full_name() or obj.related_message.sender.email,
                'thread_id': obj.related_message.thread.id,
                'thread_subject': obj.related_message.thread.subject
            }
        return None


class NotificationSerializer(serializers.ModelSerializer):
    """
    Base notification serializer for create and update operations.
    """
    class Meta:
        model = Notification
        exclude = ['read_at', 'sent_at']
        read_only_fields = ['is_read', 'is_sent', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Custom validation for notification data"""
        # For certain notification types, validate related entities
        notification_type = data.get('notification_type')
        
        if notification_type == 'auction_start' and not data.get('related_auction'):
            raise serializers.ValidationError(_("Auction start notification requires a related auction"))
        
        if notification_type == 'auction_end' and not data.get('related_auction'):
            raise serializers.ValidationError(_("Auction end notification requires a related auction"))
        
        if notification_type == 'new_bid' and not data.get('related_bid'):
            raise serializers.ValidationError(_("New bid notification requires a related bid"))
        
        if notification_type == 'payment' and not data.get('related_payment'):
            raise serializers.ValidationError(_("Payment notification requires a related payment"))
        
        if notification_type == 'message' and not data.get('related_message'):
            raise serializers.ValidationError(_("Message notification requires a related message"))
        
        return data