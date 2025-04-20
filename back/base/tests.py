from accounts.models import CustomUser, Role
from base.models import (
    Property, Auction, Bid, Document, Contract,
    Transaction, MessageThread, 
    Message, ThreadParticipant, Notification
)
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.contenttypes.models import ContentType
from datetime import date
from django.test import TestCase
from base.models import Media


# -------------------------------------------------------------------------
# Document Model Tests
# -------------------------------------------------------------------------


class DocumentModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='testdocuser', email='doc@test.com', password='password'
        )
        cls.property = Property.objects.create(
            title="Test Property for Docs",
            property_number="PROP-DOC-001",
            description="A test property.",
            address="123 Doc St",
            city="Testville",
            property_type='residential',
            owner=cls.user,
            price=100000.00
        )
        cls.document = Document.objects.create(
            document_number="DOC12345",
            title="Test Deed",
            document_type='deed',
            uploaded_by=cls.user,
            related_property=cls.property,
            verification_status='pending',
            issue_date=date(2023, 1, 1)
        )
        # Create a dummy file for Media relation
        cls.content_type = ContentType.objects.get_for_model(Document)
        cls.media_file = SimpleUploadedFile("test_doc_file.pdf", b"file_content", content_type="application/pdf")
        cls.media = Media.objects.create(
            file=cls.media_file,
            content_type=cls.content_type,
            object_id=cls.document.id,
            media_type='document'
        )

    def test_document_creation(self):
        self.assertEqual(self.document.document_number, "DOC12345")
        self.assertEqual(self.document.title, "Test Deed")
        self.assertEqual(self.document.get_document_type_display(), 'صك ملكية')
        self.assertEqual(self.document.uploaded_by, self.user)
        self.assertEqual(self.document.related_property, self.property)
        self.assertEqual(self.document.get_verification_status_display(), 'قيد الانتظار')
        self.assertTrue(isinstance(self.document, Document))

    def test_document_str_representation(self):
        self.assertEqual(str(self.document), "Test Deed")

    def test_document_media_relation(self):
        self.assertEqual(self.document.media.count(), 1)
        media_instance = self.document.media.first()
        self.assertEqual(media_instance.file.name.split('/')[-1], "test_doc_file.pdf")
        self.assertEqual(media_instance.media_type, 'document')


# -------------------------------------------------------------------------
# Contract Model Tests
# -------------------------------------------------------------------------


class ContractModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.seller = CustomUser.objects.create_user(
            username='testseller', email='seller@test.com', password='password', user_type='seller'
        )
        cls.buyer = CustomUser.objects.create_user(
            username='testbuyer', email='buyer@test.com', password='password', user_type='buyer'
        )
        cls.property = Property.objects.create(
            title="Test Property for Contract",
            property_number="PROP-CON-001",
            description="A test property for contracting.",
            address="456 Contract Ave",
            city="Testville",
            property_type='commercial',
            owner=cls.seller, # Seller owns the property initially
            price=250000.00
        )
        cls.contract = Contract.objects.create(
            contract_number="CON98765",
            title="Sale Contract for PROP-CON-001",
            status='pending',
            related_property=cls.property,
            buyer=cls.buyer,
            seller=cls.seller,
            contract_date=date(2023, 5, 10),
            total_amount=240000.00,
            payment_method='full_payment'
        )
        # Create a dummy file for Media relation
        cls.content_type = ContentType.objects.get_for_model(Contract)
        cls.media_file = SimpleUploadedFile("test_contract_file.pdf", b"contract_content", content_type="application/pdf")
        cls.media = Media.objects.create(
            file=cls.media_file,
            content_type=cls.content_type,
            object_id=cls.contract.id,
            media_type='document' # Contracts are documents
        )

    def test_contract_creation(self):
        self.assertEqual(self.contract.contract_number, "CON98765")
        self.assertEqual(self.contract.title, "Sale Contract for PROP-CON-001")
        self.assertEqual(self.contract.get_status_display(), 'بانتظار الموافقة')
        self.assertEqual(self.contract.related_property, self.property)
        self.assertEqual(self.contract.buyer, self.buyer)
        self.assertEqual(self.contract.seller, self.seller)
        self.assertEqual(self.contract.total_amount, 240000.00)
        self.assertEqual(self.contract.get_payment_method_display(), 'دفعة كاملة')
        self.assertTrue(isinstance(self.contract, Contract))

    def test_contract_str_representation(self):
        # The default __str__ returns the title
        self.assertEqual(str(self.contract), "Sale Contract for PROP-CON-001")

    def test_contract_media_relation(self):
        self.assertEqual(self.contract.media.count(), 1)
        media_instance = self.contract.media.first()
        self.assertEqual(media_instance.file.name.split('/')[-1], "test_contract_file.pdf")
        self.assertEqual(media_instance.media_type, 'document')


# -------------------------------------------------------------------------
# Notification Model Tests
# -------------------------------------------------------------------------