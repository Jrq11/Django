from django.urls import path
from dashboard.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<int:user_id>/", ChatConsumer.as_asgi()),
]
