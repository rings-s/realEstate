# back/routing.py

from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from consumers.middleware import JwtAuthMiddleware, MetricsMiddleware
from consumers.auction_consumer import AuctionConsumer
from consumers.bidding_consumer import BiddingConsumer
from consumers.chat_consumer import ChatConsumer
from consumers.dashboard_consumer import DashboardConsumer
from consumers.notification_consumer import NotificationConsumer

# URL routes for WebSocket connections
websocket_urlpatterns = [
    # Auction WebSocket paths
    path('ws/auctions/<str:auction_id>/', AuctionConsumer.as_asgi()),

    # Bidding WebSocket paths
    path('ws/bidding/<str:auction_id>/', BiddingConsumer.as_asgi()),

    # Chat WebSocket paths
    path('ws/chat/<str:room_name>/', ChatConsumer.as_asgi()),

    # Dashboard WebSocket paths
    path('ws/dashboard/<str:user_id>/', DashboardConsumer.as_asgi()),

    # Notification WebSocket paths
    path('ws/notifications/<str:user_id>/', NotificationConsumer.as_asgi()),
]

# Apply JWT and metrics middleware to WebSocket connections
websocket_application = JwtAuthMiddleware(
    MetricsMiddleware(
        URLRouter(websocket_urlpatterns)
    )
)

# Configure the ASGI application
application = ProtocolTypeRouter({
    'websocket': websocket_application,
})
