from rest_framework import serializers
from .models import ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'content', 'image', 'file', 'audio', 'voice', 'is_admin', 'created_at']
        read_only_fields = ['user', 'is_admin', 'created_at', 'is_sent', "is_read"]
