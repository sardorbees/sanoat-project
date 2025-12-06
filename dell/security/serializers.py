from rest_framework import serializers

class BlockIPSerializer(serializers.Serializer):
    ip = serializers.CharField(max_length=45)
    reason = serializers.CharField(max_length=200, required=False, allow_blank=True)
    minutes = serializers.IntegerField(required=False, default=60)  # время блокировки

class CheckIPSerializer(serializers.Serializer):
    ip = serializers.CharField(max_length=45)

class AttackLogSerializer(serializers.Serializer):
    ip = serializers.CharField()
    path = serializers.CharField()
    message = serializers.CharField()
    created_at = serializers.DateTimeField()


from rest_framework import serializers
from .models import UserSession

class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ['session_key', 'ip_address', 'user_agent', 'created_at', 'ended_at', 'is_active']
