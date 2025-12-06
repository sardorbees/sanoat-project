from django.urls import path, include
from .views import ChatMessageListCreateView, mark_read, ChatView, ping, get_online_status
from . import views

urlpatterns = [
    path("chat/", ChatMessageListCreateView.as_view(), name="chat-list-create"),
    path("chat/<int:pk>/mark_read/", mark_read, name="chat-mark-read"),
    path("chat/", ChatView.as_view(), name="chats"),
    path('', views.chat_page, name='chat_page'),
    path("ping/", ping, name="ping"),
    path("status/<int:user_id>/", get_online_status),
]
