from django.urls import path
from . import views

app_name = 'auction_platform'

urlpatterns = [
    # Property URLs
    path('properties/', views.PropertyListCreateView.as_view(), name='property-list'),
    path('properties/<slug:slug>/', views.PropertyDetailView.as_view(), name='property-detail'),
    path('properties/<slug:slug>/edit/', views.PropertyEditView.as_view(), name='property-edit'),
    path('properties/<slug:slug>/delete/', views.PropertyDeleteView.as_view(), name='property-delete'),
    path('properties/<int:property_id>/images/', views.PropertyImageListCreateView.as_view(), name='property-image-list'),
    path('property-images/<int:pk>/', views.PropertyImageDetailView.as_view(), name='property-image-detail'),
    path('property-images/<int:pk>/edit/', views.PropertyImageEditView.as_view(), name='property-image-edit'),
    path('property-images/<int:pk>/delete/', views.PropertyImageDeleteView.as_view(), name='property-image-delete'),

    # Auction URLs
    path('auctions/', views.AuctionListCreateView.as_view(), name='auction-list'),
    path('auctions/<slug:slug>/', views.AuctionDetailView.as_view(), name='auction-detail'),
    path('auctions/<slug:slug>/edit/', views.AuctionEditView.as_view(), name='auction-edit'),
    path('auctions/<slug:slug>/delete/', views.AuctionDeleteView.as_view(), name='auction-delete'),
    path('auctions/<int:auction_id>/images/', views.AuctionImageListCreateView.as_view(), name='auction-image-list'),
    path('auction-images/<int:pk>/', views.AuctionImageDetailView.as_view(), name='auction-image-detail'),
    path('auction-images/<int:pk>/edit/', views.AuctionImageEditView.as_view(), name='auction-image-edit'),
    path('auction-images/<int:pk>/delete/', views.AuctionImageDeleteView.as_view(), name='auction-image-delete'),

    # Bid URLs
    path('auctions/<int:auction_id>/bids/', views.BidListCreateView.as_view(), name='bid-list'),
    path('bids/<int:pk>/', views.BidDetailView.as_view(), name='bid-detail'),
    path('bids/<int:pk>/edit/', views.BidEditView.as_view(), name='bid-edit'),
    path('bids/<int:pk>/delete/', views.BidDeleteView.as_view(), name='bid-delete'),
    path('auctions/<int:auction_id>/bid-suggestions/', views.BidSuggestionsView.as_view(), name='bid-suggestions'),

    # Document URLs
    path('documents/', views.DocumentListCreateView.as_view(), name='document-list'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<int:pk>/edit/', views.DocumentEditView.as_view(), name='document-edit'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document-delete'),

    # Contract URLs
    path('contracts/', views.ContractListCreateView.as_view(), name='contract-list'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract-detail'),
    path('contracts/<int:pk>/edit/', views.ContractEditView.as_view(), name='contract-edit'),
    path('contracts/<int:pk>/delete/', views.ContractDeleteView.as_view(), name='contract-delete'),

    # Message Thread URLs
    path('threads/', views.MessageThreadListCreateView.as_view(), name='thread-list'),
    path('threads/<int:pk>/', views.MessageThreadDetailView.as_view(), name='thread-detail'),
    path('threads/<int:pk>/edit/', views.MessageThreadEditView.as_view(), name='thread-edit'),
    path('threads/<int:pk>/delete/', views.MessageThreadDeleteView.as_view(), name='thread-delete'),
    path('threads/<int:thread_id>/participants/', views.ThreadParticipantListView.as_view(), name='thread-participant-list'),
    path('thread-participants/<int:pk>/', views.ThreadParticipantDetailView.as_view(), name='thread-participant-detail'),
    path('thread-participants/<int:pk>/edit/', views.ThreadParticipantEditView.as_view(), name='thread-participant-edit'),
    path('thread-participants/<int:pk>/delete/', views.ThreadParticipantDeleteView.as_view(), name='thread-participant-delete'),
    path('threads/<int:thread_id>/messages/', views.MessageListCreateView.as_view(), name='message-list'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message-detail'),
    path('messages/<int:pk>/edit/', views.MessageEditView.as_view(), name='message-edit'),
    path('messages/<int:pk>/delete/', views.MessageDeleteView.as_view(), name='message-delete'),

    # Notification URLs
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<int:pk>/edit/', views.NotificationEditView.as_view(), name='notification-edit'),
    path('notifications/<int:pk>/delete/', views.NotificationDeleteView.as_view(), name='notification-delete'),

    # Property View URLs (like floor plans, street views)
    path('auctions/<int:auction_id>/property-views/', views.PropertyViewListCreateView.as_view(), name='property-view-list'),
    path('property-views/<int:pk>/', views.PropertyViewDetailView.as_view(), name='property-view-detail'),
    path('property-views/<int:pk>/edit/', views.PropertyViewEditView.as_view(), name='property-view-edit'),
    path('property-views/<int:pk>/delete/', views.PropertyViewDeleteView.as_view(), name='property-view-delete'),
]
