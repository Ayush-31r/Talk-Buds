from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r"room/(?P<room_id>\d+)/$", ChatConsumer.as_asgi()),  # Allow only numbers
]
