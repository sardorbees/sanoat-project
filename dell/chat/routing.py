from django.urls import re_path
from . import consumers, ChatOnlineConsumer, ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/?$', consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/chat/(?P<user_id>\d+)/$", ChatOnlineConsumer.as_asgi()),
    re_path("ws/chat/", ChatConsumer.as_asgi()),
    re_path(r"ws/chat/(?P<user_id>\d+)/$", consumers.ChatConsumer.as_asgi()),
    re_path("ws/chat/<int:user_id>/", ChatConsumer.as_asgi()),
]
