from django.urls import path, register_converter

from .views import (
    # Property views
    PropertyListCreateView, PropertyDetailView, PropertyBySlugView, VerifyPropertyView, MyPropertiesView,
    UploadPropertyImagesView,

    # Auction views
    AuctionListCreateView, AuctionDetailView, AuctionBySlugView, PlaceBidView, ExtendAuctionView,
    CloseAuctionView, MyAuctionsView, UploadAuctionImagesView,

    # Bid views
    BidListCreateView, BidDetailView, MarkBidAsWinningView, MyBidsView,

    # Document views
    DocumentListCreateView, DocumentDetailView, VerifyDocumentView, MyDocumentsView,
    UploadDocumentFilesView,

    # Contract views
    ContractListCreateView, ContractDetailView, SignContractAsBuyerView, SignContractAsSellerView,
    SignContractAsAgentView, MyContractsView, UploadContractFilesView,

    # Payment views
    PaymentListCreateView, PaymentDetailView, ConfirmPaymentView, MyPaymentsView,
    UploadPaymentReceiptView,

    # Message Thread views
    MessageThreadListCreateView, MessageThreadDetailView, ThreadBySlugView, AddThreadParticipantView,
    RemoveThreadParticipantView, MarkThreadAsReadView, CloseThreadView, ReopenThreadView, MyThreadsView,

    # Message views
    MessageListCreateView, MessageDetailView, MarkMessageAsReadView, MyMessagesView,
    UploadMessageAttachmentView,

    # Transaction views
    TransactionListCreateView, TransactionDetailView, MarkTransactionAsCompletedView,
    MarkTransactionAsFailedView, MyTransactionsView,

    # Notification views
    NotificationListCreateView, NotificationDetailView, MarkNotificationAsReadView,
    MarkAllNotificationsAsReadView, MyNotificationsView
)


class ArabicSlugConverter:
    regex = r'[\w\d\-\u0621-\u064A]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(ArabicSlugConverter, 'arabic_slug')


urlpatterns = [
    # Property URLs
    path('properties/', PropertyListCreateView.as_view(), name='property-list'),
    path('properties/<int:pk>/', PropertyDetailView.as_view(), name='property-detail'),
    path('properties/by-slug/<arabic_slug:slug>/', PropertyBySlugView.as_view(), name='property-detail-by-slug'),
    path('properties/<int:pk>/verify/', VerifyPropertyView.as_view(), name='property-verify'),
    path('properties/my-properties/', MyPropertiesView.as_view(), name='property-my-properties'),
    path('properties/<int:pk>/upload-images/', UploadPropertyImagesView.as_view(), name='property-upload-images'),

    # Auction URLs
    path('auctions/', AuctionListCreateView.as_view(), name='auction-list'),
    path('auctions/<int:pk>/', AuctionDetailView.as_view(), name='auction-detail'),
    path('auctions/by-slug/<arabic_slug:slug>/', AuctionBySlugView.as_view(), name='auction-detail-by-slug'),
    path('auctions/<int:pk>/place-bid/', PlaceBidView.as_view(), name='auction-place-bid'),
    path('auctions/<int:pk>/extend/', ExtendAuctionView.as_view(), name='auction-extend'),
    path('auctions/<int:pk>/close/', CloseAuctionView.as_view(), name='auction-close'),
    path('auctions/my-auctions/', MyAuctionsView.as_view(), name='auction-my-auctions'),
    path('auctions/<int:pk>/upload-images/', UploadAuctionImagesView.as_view(), name='auction-upload-images'),

    # Bid URLs
    path('bids/', BidListCreateView.as_view(), name='bid-list'),
    path('bids/<int:pk>/', BidDetailView.as_view(), name='bid-detail'),
    path('bids/<int:pk>/mark-winning/', MarkBidAsWinningView.as_view(), name='bid-mark-winning'),
    path('bids/my-bids/', MyBidsView.as_view(), name='bid-my-bids'),

    # Document URLs
    path('documents/', DocumentListCreateView.as_view(), name='document-list'),
    path('documents/<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<int:pk>/verify/', VerifyDocumentView.as_view(), name='document-verify'),
    path('documents/my-documents/', MyDocumentsView.as_view(), name='document-my-documents'),
    path('documents/<int:pk>/upload-files/', UploadDocumentFilesView.as_view(), name='document-upload-files'),

    # Contract URLs
    path('contracts/', ContractListCreateView.as_view(), name='contract-list'),
    path('contracts/<int:pk>/', ContractDetailView.as_view(), name='contract-detail'),
    path('contracts/<int:pk>/sign-buyer/', SignContractAsBuyerView.as_view(), name='contract-sign-buyer'),
    path('contracts/<int:pk>/sign-seller/', SignContractAsSellerView.as_view(), name='contract-sign-seller'),
    path('contracts/<int:pk>/sign-agent/', SignContractAsAgentView.as_view(), name='contract-sign-agent'),
    path('contracts/my-contracts/', MyContractsView.as_view(), name='contract-my-contracts'),
    path('contracts/<int:pk>/upload-files/', UploadContractFilesView.as_view(), name='contract-upload-files'),

    # Payment URLs
    path('payments/', PaymentListCreateView.as_view(), name='payment-list'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/<int:pk>/confirm/', ConfirmPaymentView.as_view(), name='payment-confirm'),
    path('payments/my-payments/', MyPaymentsView.as_view(), name='payment-my-payments'),
    path('payments/<int:pk>/upload-receipt/', UploadPaymentReceiptView.as_view(), name='payment-upload-receipt'),

    # Message Thread URLs
    path('message-threads/', MessageThreadListCreateView.as_view(), name='messagethread-list'),
    path('message-threads/<int:pk>/', MessageThreadDetailView.as_view(), name='messagethread-detail'),
    path('message-threads/by-slug/<arabic_slug:slug>/', ThreadBySlugView.as_view(), name='message-thread-detail-by-slug'),
    path('message-threads/<int:pk>/add-participant/', AddThreadParticipantView.as_view(), name='message-thread-add-participant'),
    path('message-threads/<int:pk>/remove-participant/', RemoveThreadParticipantView.as_view(), name='message-thread-remove-participant'),
    path('message-threads/<int:pk>/mark-read/', MarkThreadAsReadView.as_view(), name='message-thread-mark-read'),
    path('message-threads/<int:pk>/close/', CloseThreadView.as_view(), name='message-thread-close'),
    path('message-threads/<int:pk>/reopen/', ReopenThreadView.as_view(), name='message-thread-reopen'),
    path('message-threads/my-threads/', MyThreadsView.as_view(), name='message-thread-my-threads'),

    # Message URLs
    path('messages/', MessageListCreateView.as_view(), name='message-list'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    path('messages/<int:pk>/mark-read/', MarkMessageAsReadView.as_view(), name='message-mark-read'),
    path('messages/my-messages/', MyMessagesView.as_view(), name='message-my-messages'),
    path('messages/<int:pk>/upload-attachment/', UploadMessageAttachmentView.as_view(), name='message-upload-attachment'),

    # Transaction URLs
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('transactions/<int:pk>/mark-completed/', MarkTransactionAsCompletedView.as_view(), name='transaction-mark-completed'),
    path('transactions/<int:pk>/mark-failed/', MarkTransactionAsFailedView.as_view(), name='transaction-mark-failed'),
    path('transactions/my-transactions/', MyTransactionsView.as_view(), name='transaction-my-transactions'),

    # Notification URLs
    path('notifications/', NotificationListCreateView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<int:pk>/mark-read/', MarkNotificationAsReadView.as_view(), name='notification-mark-read'),
    path('notifications/mark-all-read/', MarkAllNotificationsAsReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/my-notifications/', MyNotificationsView.as_view(), name='notification-my-notifications'),
]



"""
/properties/${id}/upload-images/
/auctions/${id}/upload-images/
/documents/${id}/upload-files/
/contracts/${id}/upload-files/
/payments/${id}/upload-receipt/
/messages/${id}/upload-attachment/


"""
