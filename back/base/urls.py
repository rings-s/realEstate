from django.urls import path, register_converter

from .views import (
    # Base API views
    BaseAPIView, BaseUploadView, MediaUploadView,

    # Property views
    PropertyListCreateView, PropertyDetailView, PropertyBySlugView, VerifyPropertyView, MyPropertiesView,
    PropertyImageUploadView, PropertyImageSetPrimaryView, PropertyImageDeleteView,

    # Auction views
    AuctionListCreateView, AuctionDetailView, AuctionBySlugView, PlaceBidView, ExtendAuctionView,
    CloseAuctionView, MyAuctionsView, AuctionImageUploadView,

    # Bid views
    BidListCreateView, BidDetailView, MarkBidAsWinningView, MyBidsView,

    # Document views
    DocumentListCreateView, DocumentDetailView, VerifyDocumentView, MyDocumentsView,
    DocumentFileUploadView,

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
    # List/Create endpoints - consistent pattern: /{resource}/
    path('properties/', PropertyListCreateView.as_view(), name='property-list'),
    path('auctions/', AuctionListCreateView.as_view(), name='auction-list'),
    path('bids/', BidListCreateView.as_view(), name='bid-list'),
    path('documents/', DocumentListCreateView.as_view(), name='document-list'),
    path('contracts/', ContractListCreateView.as_view(), name='contract-list'),
    path('payments/', PaymentListCreateView.as_view(), name='payment-list'),
    path('threads/', MessageThreadListCreateView.as_view(), name='thread-list'),
    path('messages/', MessageListCreateView.as_view(), name='message-list'),
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list'),
    path('notifications/', NotificationListCreateView.as_view(), name='notification-list'),

    # Detail endpoints - consistent pattern: /{resource}/{id}/
    path('properties/<int:pk>/', PropertyDetailView.as_view(), name='property-detail'),
    path('auctions/<int:pk>/', AuctionDetailView.as_view(), name='auction-detail'),
    path('bids/<int:pk>/', BidDetailView.as_view(), name='bid-detail'),
    path('documents/<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('contracts/<int:pk>/', ContractDetailView.as_view(), name='contract-detail'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('threads/<int:pk>/', MessageThreadDetailView.as_view(), name='thread-detail'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),

    # Slug-based detail endpoints - consistent pattern: /{resource}/slug/{slug}/
    path('properties/slug/<arabic_slug:slug>/', PropertyBySlugView.as_view(), name='property-by-slug'),
    path('auctions/slug/<arabic_slug:slug>/', AuctionBySlugView.as_view(), name='auction-by-slug'),
    path('threads/slug/<arabic_slug:slug>/', ThreadBySlugView.as_view(), name='thread-by-slug'),

    # My resources endpoints - consistent pattern: /{resource}/my/
    path('properties/my/', MyPropertiesView.as_view(), name='my-properties'),
    path('auctions/my/', MyAuctionsView.as_view(), name='my-auctions'),
    path('bids/my/', MyBidsView.as_view(), name='my-bids'),
    path('documents/my/', MyDocumentsView.as_view(), name='my-documents'),
    path('contracts/my/', MyContractsView.as_view(), name='my-contracts'),
    path('payments/my/', MyPaymentsView.as_view(), name='my-payments'),
    path('threads/my/', MyThreadsView.as_view(), name='my-threads'),
    path('messages/my/', MyMessagesView.as_view(), name='my-messages'),
    path('transactions/my/', MyTransactionsView.as_view(), name='my-transactions'),
    path('notifications/my/', MyNotificationsView.as_view(), name='my-notifications'),

    # Upload endpoints - consistent pattern: /{resource}/{id}/uploads/
    path('properties/<int:pk>/uploads/', PropertyImageUploadView.as_view(), name='property-upload'),
    path('auctions/<int:pk>/uploads/', AuctionImageUploadView.as_view(), name='auction-upload'),
    path('documents/<int:pk>/uploads/', DocumentFileUploadView.as_view(), name='document-upload'),
    path('contracts/<int:pk>/uploads/', UploadContractFilesView.as_view(), name='contract-upload'),
    path('payments/<int:pk>/uploads/', UploadPaymentReceiptView.as_view(), name='payment-upload'),
    path('messages/<int:pk>/uploads/', UploadMessageAttachmentView.as_view(), name='message-upload'),

    # Action endpoints - consistent pattern: /{resource}/{id}/actions/{action}/
    # Property actions
    path('properties/<int:pk>/actions/verify/', VerifyPropertyView.as_view(), name='property-verify'),
    path('properties/<int:pk>/actions/set-primary-image/', PropertyImageSetPrimaryView.as_view(), name='property-set-primary-image'),
    path('properties/<int:pk>/actions/delete-image/<int:image_index>/', PropertyImageDeleteView.as_view(), name='property-delete-image'),

    # Auction actions
    path('auctions/<int:pk>/actions/bid/', PlaceBidView.as_view(), name='auction-bid'),
    path('auctions/<int:pk>/actions/extend/', ExtendAuctionView.as_view(), name='auction-extend'),
    path('auctions/<int:pk>/actions/close/', CloseAuctionView.as_view(), name='auction-close'),

    # Bid actions
    path('bids/<int:pk>/actions/mark-winning/', MarkBidAsWinningView.as_view(), name='bid-mark-winning'),

    # Document actions
    path('documents/<int:pk>/actions/verify/', VerifyDocumentView.as_view(), name='document-verify'),

    # Contract actions
    path('contracts/<int:pk>/actions/sign-buyer/', SignContractAsBuyerView.as_view(), name='contract-sign-buyer'),
    path('contracts/<int:pk>/actions/sign-seller/', SignContractAsSellerView.as_view(), name='contract-sign-seller'),
    path('contracts/<int:pk>/actions/sign-agent/', SignContractAsAgentView.as_view(), name='contract-sign-agent'),

    # Payment actions
    path('payments/<int:pk>/actions/confirm/', ConfirmPaymentView.as_view(), name='payment-confirm'),

    # Thread actions
    path('threads/<int:pk>/actions/add-participant/', AddThreadParticipantView.as_view(), name='thread-add-participant'),
    path('threads/<int:pk>/actions/remove-participant/', RemoveThreadParticipantView.as_view(), name='thread-remove-participant'),
    path('threads/<int:pk>/actions/mark-read/', MarkThreadAsReadView.as_view(), name='thread-mark-read'),
    path('threads/<int:pk>/actions/close/', CloseThreadView.as_view(), name='thread-close'),
    path('threads/<int:pk>/actions/reopen/', ReopenThreadView.as_view(), name='thread-reopen'),

    # Message actions
    path('messages/<int:pk>/actions/mark-read/', MarkMessageAsReadView.as_view(), name='message-mark-read'),

    # Transaction actions
    path('transactions/<int:pk>/actions/mark-completed/', MarkTransactionAsCompletedView.as_view(), name='transaction-mark-completed'),
    path('transactions/<int:pk>/actions/mark-failed/', MarkTransactionAsFailedView.as_view(), name='transaction-mark-failed'),

    # Notification actions
    path('notifications/<int:pk>/actions/mark-read/', MarkNotificationAsReadView.as_view(), name='notification-mark-read'),
    path('notifications/actions/mark-all-read/', MarkAllNotificationsAsReadView.as_view(), name='notification-mark-all-read'),
]
