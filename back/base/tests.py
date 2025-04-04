# tests/test_models.py

import json
from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from accounts.models import CustomUser, Role
from base.models import (
    Property, Auction, Bid, Document, Contract,
    Payment, Transaction, PropertyView, MessageThread,
    Message, ThreadParticipant, Notification
)


class BaseModelTestCase(TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        # Create test roles first
        self.admin_role = Role.objects.create(name=Role.ADMIN, description='Admin role')
        self.seller_role = Role.objects.create(name=Role.SELLER, description='Seller role')
        self.buyer_role = Role.objects.create(name=Role.BUYER, description='Buyer role')
        
        # Create test users
        self.user1 = CustomUser.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User1'
        )
        self.user1.roles.add(self.seller_role)
        
        self.user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User2'
        )
        self.user2.roles.add(self.buyer_role)
        
        self.admin_user = CustomUser.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True
        )
        self.admin_user.roles.add(self.admin_role)


class PropertyModelTest(BaseModelTestCase):
    """Test cases for the Property model"""
    
    def setUp(self):
        super().setUp()
        # Create a basic property for testing
        self.property = Property.objects.create(
            title='Test Property',
            property_type='apartment',
            owner=self.user1,
            address='123 Test St',
            city='Test City',
            district='Test District',
            area=Decimal('100.00'),
            estimated_value=Decimal('500000.00'),
        )
    
    def test_property_creation(self):
        """Test that property is created correctly"""
        self.assertIsNotNone(self.property.pk)
        self.assertEqual(self.property.title, 'Test Property')
        self.assertEqual(self.property.property_type, 'apartment')
        self.assertEqual(self.property.status, 'draft')  # Default status
        self.assertIsNotNone(self.property.property_number)
        self.assertIsNotNone(self.property.slug)
    
    def test_property_string_representation(self):
        """Test the string representation of a property"""
        expected = f"{self.property.property_number} - Test Property"
        self.assertEqual(str(self.property), expected)
    
    def test_json_field_handling(self):
        """Test JSON field serialization and deserialization"""
        # Set JSON fields
        images_data = [
            {'path': '/images/test1.jpg', 'is_primary': True},
            {'path': '/images/test2.jpg', 'is_primary': False}
        ]
        
        features_data = [
            'Swimming Pool',
            'Garden',
            'Garage'
        ]
        
        location_data = {
            'latitude': 25.123456,
            'longitude': 55.654321
        }
        
        # Set as JSON strings (SQLite compatibility)
        self.property.images = json.dumps(images_data)
        self.property.features = json.dumps(features_data)
        self.property.location = json.dumps(location_data)
        self.property.save()
        
        # Reload from database
        property_reloaded = Property.objects.get(pk=self.property.pk)
        
        # Test get_json_field method
        self.assertEqual(property_reloaded.get_json_field('images'), images_data)
        self.assertEqual(property_reloaded.get_json_field('features'), features_data)
        self.assertEqual(property_reloaded.get_json_field('location'), location_data)
        
        # Test property methods
        self.assertEqual(property_reloaded.location_dict, location_data)
        self.assertEqual(property_reloaded.main_image_url, '/images/test1.jpg')
        
    def test_price_per_sqm_calculation(self):
        """Test that price_per_sqm is calculated correctly"""
        # Initially calculated on save
        self.assertEqual(self.property.price_per_sqm, self.property.estimated_value / self.property.area)
        
        # Update values and check recalculation
        self.property.estimated_value = Decimal('600000.00')
        self.property.save()
        self.assertEqual(self.property.price_per_sqm, Decimal('6000.00'))


class AuctionModelTest(BaseModelTestCase):
    """Test cases for the Auction model"""
    
    def setUp(self):
        super().setUp()
        # Create property for auction
        self.property = Property.objects.create(
            title='Auction Property',
            property_type='apartment',
            owner=self.user1,
            address='123 Auction St',
            city='Auction City',
            district='Auction District',
            area=Decimal('100.00'),
            estimated_value=Decimal('500000.00'),
        )
        
        # Create auction
        now = timezone.now()
        self.auction = Auction.objects.create(
            title='Test Auction',
            related_property=self.property,
            created_by=self.user1,
            auctioneer=self.user1,
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=8),
            starting_price=Decimal('400000.00'),
            reserve_price=Decimal('450000.00'),
            min_bid_increment=Decimal('5000.00'),
            auction_type='online',
        )
    
    def test_auction_creation(self):
        """Test that auction is created correctly"""
        self.assertIsNotNone(self.auction.pk)
        self.assertEqual(self.auction.title, 'Test Auction')
        self.assertEqual(self.auction.status, 'draft')  # Default status
        self.assertIsNotNone(self.auction.uuid)
        self.assertIsNotNone(self.auction.slug)
    
    def test_json_field_handling(self):
        """Test JSON field handling for auction"""
        # Set JSON fields
        images_data = [
            {'path': '/auctions/test1.jpg', 'is_featured': True},
            {'path': '/auctions/test2.jpg', 'is_featured': False}
        ]
        
        location_data = {
            'latitude': 25.123456,
            'longitude': 55.654321
        }
        
        # Set as JSON strings (SQLite compatibility)
        self.auction.images = json.dumps(images_data)
        self.auction.location = json.dumps(location_data)
        self.auction.save()
        
        # Reload from database
        auction_reloaded = Auction.objects.get(pk=self.auction.pk)
        
        # Test get_json_field method
        self.assertEqual(auction_reloaded.get_json_field('images'), images_data)
        self.assertEqual(auction_reloaded.get_json_field('location'), location_data)
        
        # Test property methods
        self.assertEqual(auction_reloaded.location_dict, location_data)
        self.assertEqual(auction_reloaded.featured_image_url, '/auctions/test1.jpg')
    
    def test_auction_extend(self):
        """Test extending an auction"""
        original_end_date = self.auction.end_date
        
        # Extend auction by 30 minutes
        self.auction.extend_auction(minutes=30)
        
        # Verify extension
        self.assertEqual(self.auction.status, 'extended')
        self.assertEqual(self.auction.end_date, original_end_date + timedelta(minutes=30))


class BidModelTest(BaseModelTestCase):
    """Test cases for the Bid model"""
    
    def setUp(self):
        super().setUp()
        # Create property for auction
        self.property = Property.objects.create(
            title='Bid Property',
            property_type='apartment',
            owner=self.user1,
            address='123 Bid St',
            city='Bid City',
            district='Bid District',
            area=Decimal('100.00'),
            estimated_value=Decimal('500000.00'),
        )
        
        # Create auction
        now = timezone.now()
        self.auction = Auction.objects.create(
            title='Bid Auction',
            related_property=self.property,
            created_by=self.user1,
            auctioneer=self.user1,
            start_date=now - timedelta(hours=1),  # Already started
            end_date=now + timedelta(days=7),
            starting_price=Decimal('400000.00'),
            reserve_price=Decimal('450000.00'),
            min_bid_increment=Decimal('5000.00'),
            auction_type='online',
            status='active',  # Set to active for bidding
        )
    
    def test_bid_creation_and_validation(self):
        """Test bid creation and validation"""
        # Create a valid bid
        bid = Bid(
            auction=self.auction,
            bidder=self.user2,
            bid_amount=Decimal('405000.00')
        )
        
        # Test validation works correctly
        bid.clean()  # Should not raise ValidationError
        bid.save()
        
        # Verify bid was created
        self.assertIsNotNone(bid.pk)
        self.assertEqual(bid.bid_amount, Decimal('405000.00'))
        self.assertEqual(bid.status, 'pending')
        
        # Test invalid bid amount validation
        invalid_bid = Bid(
            auction=self.auction,
            bidder=self.user2,
            bid_amount=Decimal('402000.00')  # Too small increment
        )
        
        # Should raise ValidationError due to min_bid_increment
        with self.assertRaises(ValidationError):
            invalid_bid.clean()
    
    def test_mark_as_winning(self):
        """Test marking a bid as winning"""
        # Create a bid
        bid = Bid.objects.create(
            auction=self.auction,
            bidder=self.user2,
            bid_amount=Decimal('405000.00'),
            status='pending'
        )
        
        # Mark bid as winning
        result = bid.mark_as_winning()
        
        # Verify result
        self.assertTrue(result)
        self.assertEqual(bid.status, 'winning')
        
        # Verify auction update
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.winning_bid, bid.bid_amount)
        self.assertEqual(self.auction.winning_bidder, self.user2)


class MessageThreadModelTest(BaseModelTestCase):
    """Test cases for the MessageThread model"""
    
    def setUp(self):
        super().setUp()
        # Create a property for reference
        self.property = Property.objects.create(
            title='Message Property',
            property_type='apartment',
            owner=self.user1,
            address='123 Message St',
            city='Message City',
            district='Message District',
            area=Decimal('100.00'),
            estimated_value=Decimal('500000.00'),
        )
        
        # Create a message thread
        self.thread = MessageThread.objects.create(
            subject='Property Inquiry',
            thread_type='inquiry',
            creator=self.user2,
            related_property=self.property,
        )
        
        # Add participants - use the roles from accounts.models
        self.participant1 = ThreadParticipant.objects.create(
            thread=self.thread,
            user=self.user1,
            role=self.seller_role,
        )
        
        self.participant2 = ThreadParticipant.objects.create(
            thread=self.thread,
            user=self.user2,
            role=self.buyer_role,
        )
        
        # Create a message
        self.message = Message.objects.create(
            thread=self.thread,
            sender=self.user2,
            content='Is this property still available?',
            message_type='inquiry',
        )
    
    def test_thread_creation(self):
        """Test message thread creation"""
        self.assertIsNotNone(self.thread.pk)
        self.assertEqual(self.thread.subject, 'Property Inquiry')
        self.assertEqual(self.thread.thread_type, 'inquiry')
        self.assertEqual(self.thread.status, 'active')
        self.assertIsNotNone(self.thread.uuid)
    
    def test_thread_participants(self):
        """Test thread participants property"""
        participants = self.thread.participants
        self.assertEqual(participants.count(), 2)
        self.assertIn(self.user1, participants)
        self.assertIn(self.user2, participants)
    
    def test_message_creation(self):
        """Test message creation"""
        self.assertIsNotNone(self.message.pk)
        self.assertEqual(self.message.content, 'Is this property still available?')
        self.assertEqual(self.message.sender, self.user2)
        self.assertEqual(self.message.status, 'sent')
        
        # Test thread last_message_at update
        self.assertEqual(self.thread.last_message_at, self.message.sent_at)
    
    def test_mark_message_as_read(self):
        """Test marking a message as read"""
        # Initial state
        self.assertEqual(self.message.status, 'sent')
        self.assertIsNone(self.message.read_at)
        
        # Mark as read
        result = self.message.mark_as_read(self.user1)
        
        # Verify result
        self.assertTrue(result)
        self.assertEqual(self.message.status, 'read')
        self.assertIsNotNone(self.message.read_at)


class NotificationModelTest(BaseModelTestCase):
    """Test cases for the Notification model"""
    
    def setUp(self):
        super().setUp()
        # Create a property
        self.property = Property.objects.create(
            title='Notification Property',
            property_type='apartment',
            owner=self.user1,
            address='123 Notification St',
            city='Notification City',
            district='Notification District',
            area=Decimal('100.00'),
            estimated_value=Decimal('500000.00'),
        )
        
        # Create a notification
        self.notification = Notification.objects.create(
            recipient=self.user1,
            notification_type='property_status',
            title='Property Status Changed',
            content='Your property has been approved',
            channel='app',
            related_property=self.property,
            icon='check-circle',
            color='success',
            action_url=f'/properties/{self.property.id}',
        )
    
    def test_notification_creation(self):
        """Test notification creation"""
        self.assertIsNotNone(self.notification.pk)
        self.assertEqual(self.notification.title, 'Property Status Changed')
        self.assertEqual(self.notification.recipient, self.user1)
        self.assertEqual(self.notification.notification_type, 'property_status')
        self.assertFalse(self.notification.is_read)
        self.assertFalse(self.notification.is_sent)
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        # Initial state
        self.assertFalse(self.notification.is_read)
        self.assertIsNone(self.notification.read_at)
        
        # Mark as read
        result = self.notification.mark_as_read()
        
        # Verify result
        self.assertTrue(result)
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)