from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum
import json
from datetime import timedelta

from .models import (
    Property, Auction, Bid, Document, Contract, Payment, Transaction,
    PropertyView, MessageThread, Message, ThreadParticipant, Notification
)
from accounts.models import CustomUser


class JsonSerializerMixin:
    """Mixin to handle JSON fields stored as text for SQLite compatibility"""
    def get_json_field(self, obj, field_name, default=None):
        """Parse JSON field or return default value"""
        value = getattr(obj, field_name, None)
        if not value:
            return default if default is not None else (
                [] if field_name in ['images', 'videos', 'features', 'amenities', 'files', 'attachments'] else {}
            )

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default if default is not None else (
                [] if field_name in ['images', 'videos', 'features', 'amenities', 'files', 'attachments'] else {}
            )

    def to_json_field(self, data, field_name):
        """Convert field to JSON string if it's a dict or list"""
        if field_name in data and data[field_name]:
            if isinstance(data[field_name], (dict, list)):
                data = data.copy() if hasattr(data, '_mutable') else data
                data[field_name] = json.dumps(data[field_name])
        return data


class UserSerializer(serializers.ModelSerializer):
    """Simple user serializer"""
    name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name']

    def get_name(self, obj):
        return obj.get_full_name() or obj.email


class PropertySerializer(JsonSerializerMixin, serializers.ModelSerializer):
    """Property serializer"""
    # Display fields
    owner_name = serializers.SerializerMethodField(read_only=True)
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # JSON fields
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    # Computed fields
    main_image_url = serializers.SerializerMethodField(read_only=True)
    has_auction = serializers.BooleanField(read_only=True)
    active_auction_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = [
            'property_number', 'slug', 'views_count', 'verified_by',
            'verification_date', 'is_verified', 'status_history',
            'publish_date', 'created_at', 'updated_at'
        ]

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() if obj.owner else None

    def get_images(self, obj):
        return self.get_json_field(obj, 'images', [])

    def get_videos(self, obj):
        return self.get_json_field(obj, 'videos', [])

    def get_features(self, obj):
        return self.get_json_field(obj, 'features', [])

    def get_amenities(self, obj):
        return self.get_json_field(obj, 'amenities', [])

    def get_location(self, obj):
        return self.get_json_field(obj, 'location', {})

    def get_main_image_url(self, obj):
        return obj.main_image_url

    def get_active_auction_id(self, obj):
        active_auction = obj.auctions.filter(status__in=['active', 'pending']).first()
        return active_auction.id if active_auction else None

    def to_internal_value(self, data):
        """Convert JSON fields to string for storage"""
        json_fields = [
            'images', 'videos', 'features', 'amenities', 'location',
            'street_details', 'rooms', 'outdoor_spaces', 'rental_details',
            'parking', 'building_services', 'infrastructure', 'surroundings',
            'reference_ids'
        ]

        # Make data mutable if needed
        if hasattr(data, '_mutable'):
            data = data.copy()

        # Convert JSON fields to strings
        for field in json_fields:
            data = self.to_json_field(data, field)

        return super().to_internal_value(data)

    def validate(self, data):
        """Validate property data"""
        # Validate numeric fields
        if 'area' in data and data['area'] <= 0:
            raise serializers.ValidationError({"area": _("Area must be greater than zero")})

        if 'estimated_value' in data and data['estimated_value'] <= 0:
            raise serializers.ValidationError({"estimated_value": _("Value must be greater than zero")})

        # Validate status transition
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status, data['status'], self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})

        return data


class AuctionSerializer(JsonSerializerMixin, serializers.ModelSerializer):
    """Auction serializer"""
    # Display fields
    property_title = serializers.CharField(source='related_property.title', read_only=True)
    auction_type_display = serializers.CharField(source='get_auction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # JSON fields
    images = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    # Computed fields
    bid_count = serializers.IntegerField(read_only=True)
    highest_bid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    time_remaining = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    featured_image_url = serializers.SerializerMethodField(read_only=True)

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

    def get_featured_image_url(self, obj):
        return obj.featured_image_url

    def to_internal_value(self, data):
        """Convert JSON fields to string for storage"""
        json_fields = ['images', 'videos', 'documents', 'location']

        # Make data mutable if needed
        if hasattr(data, '_mutable'):
            data = data.copy()

        # Convert JSON fields to strings
        for field in json_fields:
            data = self.to_json_field(data, field)

        return super().to_internal_value(data)

    def validate(self, data):
        """Validate auction data"""
        # Validate dates
        if not self.instance and 'start_date' in data:
            if data['start_date'] <= timezone.now():
                raise serializers.ValidationError({"start_date": _("Start date must be in the future")})

        if 'start_date' in data and 'end_date' in data:
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError({"end_date": _("End date must be after start date")})

        # Validate prices
        if 'starting_price' in data and data['starting_price'] <= 0:
            raise serializers.ValidationError({"starting_price": _("Starting price must be greater than zero")})

        if 'reserve_price' in data and 'starting_price' in data:
            if data['reserve_price'] < data['starting_price']:
                raise serializers.ValidationError({"reserve_price": _("Reserve price must be greater than or equal to starting price")})

        # Validate status transition
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status, data['status'], self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})

        return data


class BidSerializer(serializers.ModelSerializer):
    """Bid serializer"""
    bidder_name = serializers.SerializerMethodField(read_only=True)
    auction_title = serializers.CharField(source='auction.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Bid
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'bid_time', 'ip_address', 'user_agent']

    def get_bidder_name(self, obj):
        return obj.bidder.get_full_name() or obj.bidder.email if obj.bidder else None

    def validate(self, data):
        """Validate bid data"""
        # Validate bid amount
        if 'bid_amount' in data and data['bid_amount'] <= 0:
            raise serializers.ValidationError({"bid_amount": _("Bid amount must be greater than zero")})

        # Validate bid for active auction
        if not self.instance and 'auction' in data:
            auction = data['auction']

            # Auction must be active
            if auction.status != 'active':
                raise serializers.ValidationError(_("Cannot place bid on inactive auction"))

            # Check auction timing
            now = timezone.now()
            if now < auction.start_date or now > auction.end_date:
                raise serializers.ValidationError(_("Auction is not open for bids at this time"))

            # Check minimum bid
            min_bid = auction.highest_bid + auction.min_bid_increment
            if data.get('bid_amount', 0) < min_bid:
                raise serializers.ValidationError({
                    "bid_amount": _("Bid must be at least {}").format(min_bid)
                })

        return data


class DocumentSerializer(JsonSerializerMixin, serializers.ModelSerializer):
    """Document serializer"""
    # Display fields
    uploaded_by_name = serializers.SerializerMethodField(read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)

    # JSON fields
    files = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()

    # Computed fields
    is_expired = serializers.BooleanField(read_only=True)
    main_file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = [
            'document_number', 'verification_date', 'verified_by',
            'created_at', 'updated_at'
        ]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.email if obj.uploaded_by else None

    def get_files(self, obj):
        return self.get_json_field(obj, 'files', [])

    def get_metadata(self, obj):
        return self.get_json_field(obj, 'metadata', {})

    def get_main_file_url(self, obj):
        return obj.main_file_url

    def to_internal_value(self, data):
        """Convert JSON fields to string for storage"""
        json_fields = ['files', 'metadata']

        # Make data mutable if needed
        if hasattr(data, '_mutable'):
            data = data.copy()

        # Convert JSON fields to strings
        for field in json_fields:
            data = self.to_json_field(data, field)

        return super().to_internal_value(data)

    def validate(self, data):
        """Validate document data"""
        # Ensure document is related to at least one entity
        if not data.get('related_property') and not data.get('auction') and not data.get('contract'):
            raise serializers.ValidationError(_("Document must be related to a property, auction, or contract"))

        # Validate dates
        if 'issue_date' in data and 'expiry_date' in data and data['expiry_date'] and data['issue_date']:
            if data['expiry_date'] <= data['issue_date']:
                raise serializers.ValidationError({"expiry_date": _("Expiry date must be after issue date")})

        # Validate status transition
        if self.instance and 'verification_status' in data and data['verification_status'] != self.instance.verification_status:
            try:
                self.instance.validate_status_transition(
                    self.instance.verification_status, data['verification_status'],
                    self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"verification_status": str(e)})

        return data


class ContractSerializer(JsonSerializerMixin, serializers.ModelSerializer):
    """Contract serializer"""
    # Display fields
    buyer_name = serializers.SerializerMethodField(read_only=True)
    seller_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    # JSON fields
    files = serializers.SerializerMethodField()

    # Computed fields
    is_fully_signed = serializers.BooleanField(read_only=True)
    signing_status = serializers.SerializerMethodField(read_only=True)
    remaining_amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Contract
        fields = '__all__'
        read_only_fields = [
            'contract_number', 'buyer_signed', 'seller_signed', 'agent_signed',
            'buyer_signature_date', 'seller_signature_date', 'agent_signature_date',
            'is_verified', 'verification_authority', 'verification_date',
            'created_at', 'updated_at'
        ]

    def get_buyer_name(self, obj):
        return obj.buyer.get_full_name() or obj.buyer.email if obj.buyer else None

    def get_seller_name(self, obj):
        return obj.seller.get_full_name() or obj.seller.email if obj.seller else None

    def get_files(self, obj):
        return self.get_json_field(obj, 'files', [])

    def get_signing_status(self, obj):
        """Get contract signing status"""
        if obj.buyer_signed and obj.seller_signed and (not obj.agent or obj.agent_signed):
            return "fully_signed"
        elif obj.buyer_signed or obj.seller_signed or obj.agent_signed:
            return "partially_signed"
        return "unsigned"

    def get_remaining_amount(self, obj):
        completed_payments = obj.payments.filter(status='completed')
        total_paid = completed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
        return obj.total_amount - total_paid

    def to_internal_value(self, data):
        """Convert JSON fields to string for storage"""
        if 'files' in data and data['files']:
            data = self.to_json_field(data, 'files')

        return super().to_internal_value(data)

    def validate(self, data):
        """Validate contract data"""
        # Validate amounts
        if 'contract_amount' in data and data['contract_amount'] <= 0:
            raise serializers.ValidationError({"contract_amount": _("Contract amount must be greater than zero")})

        if 'total_amount' in data and 'contract_amount' in data:
            if data['total_amount'] < data['contract_amount']:
                raise serializers.ValidationError({"total_amount": _("Total amount must be greater than or equal to contract amount")})

        # Validate property and auction relationship
        if 'auction' in data and 'related_property' in data:
            if data['auction'].related_property.id != data['related_property'].id:
                raise serializers.ValidationError(_("Property must match the auction's property"))

        # Validate dates
        if 'contract_date' in data and 'effective_date' in data and data['effective_date']:
            if data['effective_date'] < data['contract_date']:
                raise serializers.ValidationError({"effective_date": _("Effective date must be on or after contract date")})

        # Validate status transition
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status, data['status'], self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})

        return data


class PaymentSerializer(JsonSerializerMixin, serializers.ModelSerializer):
    """Payment serializer"""
    # Display fields
    payer_name = serializers.SerializerMethodField(read_only=True)
    payee_name = serializers.SerializerMethodField(read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # JSON fields
    files = serializers.SerializerMethodField()

    # Computed fields
    is_overdue = serializers.BooleanField(read_only=True)
    receipt_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = [
            'payment_number', 'confirmed_at', 'confirmed_by',
            'created_at', 'updated_at'
        ]

    def get_payer_name(self, obj):
        return obj.payer.get_full_name() or obj.payer.email if obj.payer else None

    def get_payee_name(self, obj):
        return obj.payee.get_full_name() or obj.payee.email if obj.payee else None

    def get_files(self, obj):
        return self.get_json_field(obj, 'files', [])

    def get_receipt_url(self, obj):
        return obj.receipt_url

    def to_internal_value(self, data):
        """Convert JSON fields to string for storage"""
        if 'files' in data and data['files']:
            data = self.to_json_field(data, 'files')

        return super().to_internal_value(data)

    def validate(self, data):
        """Validate payment data"""
        # Validate amount
        if 'amount' in data and data['amount'] <= 0:
            raise serializers.ValidationError({"amount": _("Amount must be greater than zero")})

        # Validate dates
        if not self.instance and 'payment_date' in data:
            if data['payment_date'] > timezone.now() + timedelta(minutes=5):
                raise serializers.ValidationError({"payment_date": _("Payment date cannot be in the future")})

        if 'payment_date' in data and 'due_date' in data and data['due_date']:
            payment_date = data['payment_date'].date() if hasattr(data['payment_date'], 'date') else data['payment_date']
            if data['due_date'] < payment_date:
                raise serializers.ValidationError({"due_date": _("Due date must be on or after payment date")})

        # Validate roles match contract
        if 'payment_type' in data and 'contract' in data and 'payer' in data and 'payee' in data:
            payment_type = data['payment_type']
            contract = data['contract']

            if payment_type in ['deposit', 'full_payment', 'installment']:
                if data['payer'] != contract.buyer:
                    raise serializers.ValidationError({"payer": _("For {} payments, the payer must be the buyer").format(payment_type)})

                if data['payee'] != contract.seller:
                    raise serializers.ValidationError({"payee": _("For {} payments, the payee must be the seller").format(payment_type)})

        # Validate status transition
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status, data['status'], self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})

        return data


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer"""
    # Display fields
    from_user_name = serializers.SerializerMethodField(read_only=True)
    to_user_name = serializers.SerializerMethodField(read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Computed fields
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = [
            'transaction_number', 'processed_at', 'created_at', 'updated_at'
        ]

    def get_from_user_name(self, obj):
        return obj.from_user.get_full_name() or obj.from_user.email if obj.from_user else None

    def get_to_user_name(self, obj):
        return obj.to_user.get_full_name() or obj.to_user.email if obj.to_user else None

    def validate(self, data):
        """Validate transaction data"""
        # Validate amount
        if 'amount' in data and data['amount'] <= 0:
            raise serializers.ValidationError({"amount": _("Amount must be greater than zero")})

        # Validate date
        if 'transaction_date' in data:
            if data['transaction_date'] > timezone.now() + timedelta(minutes=5):
                raise serializers.ValidationError({"transaction_date": _("Transaction date cannot be in the future")})

        # Ensure at least one related entity
        if not data.get('payment') and not data.get('auction') and not data.get('contract'):
            raise serializers.ValidationError(_("Transaction must be related to a payment, auction, or contract"))

        # Validate status transition
        if self.instance and 'status' in data and data['status'] != self.instance.status:
            try:
                self.instance.validate_status_transition(
                    self.instance.status, data['status'], self.instance.STATUS_TRANSITIONS
                )
            except Exception as e:
                raise serializers.ValidationError({"status": str(e)})

        return data


class PropertyViewSerializer(JsonSerializerMixin, serializers.ModelSerializer):
    """PropertyView serializer"""
    # Display fields
    view_type_display = serializers.CharField(source='get_view_type_display', read_only=True)

    # JSON fields
    images = serializers.SerializerMethodField()
    historical_views = serializers.SerializerMethodField()

    # Computed fields
    main_image_url = serializers.SerializerMethodField(read_only=True)

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

    def to_internal_value(self, data):
        """Convert JSON fields to string for storage"""
        json_fields = ['images', 'historical_views']

        # Make data mutable if needed
        if hasattr(data, '_mutable'):
            data = data.copy()

        # Convert JSON fields to strings
        for field in json_fields:
            data = self.to_json_field(data, field)

        return super().to_internal_value(data)

    def validate(self, data):
        """Validate property view data"""
        if 'size_sqm' in data and data['size_sqm'] <= 0:
            raise serializers.ValidationError({"size_sqm": _("Size must be greater than zero")})
        return data


class ThreadParticipantSerializer(serializers.ModelSerializer):
    """Thread participant serializer"""
    user_name = serializers.SerializerMethodField(read_only=True)
    role_name = serializers.SerializerMethodField(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ThreadParticipant
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email if obj.user else None

    def get_role_name(self, obj):
        if obj.role:
            return obj.role.get_name_display()
        return _('Member')


class MessageThreadSerializer(serializers.ModelSerializer):
    """Message thread serializer"""
    # Display fields
    creator_name = serializers.SerializerMethodField(read_only=True)
    thread_type_display = serializers.CharField(source='get_thread_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Computed fields
    participants_count = serializers.SerializerMethodField(read_only=True)
    message_count = serializers.IntegerField(read_only=True)
    unread_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MessageThread
        fields = '__all__'
        read_only_fields = [
            'uuid', 'created_at', 'updated_at', 'last_message_at'
        ]

    def get_creator_name(self, obj):
        return obj.creator.get_full_name() or obj.creator.email if obj.creator else None

    def get_participants_count(self, obj):
        return obj.thread_participants.filter(is_active=True).count()

    def get_unread_count(self, obj):
        user = self.context.get('request', None)
        if not user or not user.is_authenticated:
            return 0

        participant = obj.thread_participants.filter(user=user, is_active=True).first()
        if not participant:
            return 0

        return participant.unread_count

    def validate(self, data):
        """Validate message thread data"""
        if 'status' in data and data['status'] not in ['active', 'closed', 'archived', 'deleted']:
            raise serializers.ValidationError({"status": _("Invalid status value")})
        return data


class MessageSerializer(JsonSerializerMixin, serializers.ModelSerializer):
    """Message serializer"""
    # Display fields
    sender_name = serializers.SerializerMethodField(read_only=True)
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # JSON fields
    attachments = serializers.SerializerMethodField()

    # Computed fields
    has_attachments = serializers.BooleanField(read_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = [
            'sent_at', 'delivered_at', 'read_at', 'created_at', 'updated_at'
        ]

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.email if obj.sender else None

    def get_attachments(self, obj):
        return self.get_json_field(obj, 'attachments', [])

    def to_internal_value(self, data):
        """Convert JSON fields to string for storage"""
        if 'attachments' in data and data['attachments']:
            data = self.to_json_field(data, 'attachments')

        return super().to_internal_value(data)

    def validate(self, data):
        """Validate message data"""
        # Check content is not empty
        if 'content' in data and not data['content'].strip():
            raise serializers.ValidationError({"content": _("Content cannot be empty")})

        # Validate thread participation
        if 'thread' in data and 'sender' in data:
            thread = data['thread']
            sender = data['sender']

            is_participant = ThreadParticipant.objects.filter(
                thread=thread, user=sender, is_active=True
            ).exists()

            if not is_participant and not sender.is_staff:
                raise serializers.ValidationError(_("Sender must be an active participant in the thread"))

        # Validate parent message belongs to same thread
        if 'thread' in data and 'parent_message' in data and data['parent_message']:
            if data['parent_message'].thread != data['thread']:
                raise serializers.ValidationError({"parent_message": _("Parent message must belong to the same thread")})

        return data


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    # Display fields
    recipient_name = serializers.SerializerMethodField(read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)

    # Computed fields
    is_actionable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'read_at', 'sent_at']

    def get_recipient_name(self, obj):
        return obj.recipient.get_full_name() or obj.recipient.email if obj.recipient else None

    def validate(self, data):
        """Validate notification data"""
        # Validate required related entities for specific notification types
        notification_type = data.get('notification_type')

        required_fields = {
            'auction_start': 'related_auction',
            'auction_end': 'related_auction',
            'new_bid': 'related_bid',
            'payment': 'related_payment',
            'message': 'related_message'
        }

        if notification_type in required_fields and not data.get(required_fields[notification_type]):
            field_name = required_fields[notification_type]
            raise serializers.ValidationError({field_name: _(f"{notification_type} notification requires a {field_name}")})

        return data
