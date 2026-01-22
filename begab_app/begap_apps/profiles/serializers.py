from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "nickname", "full_name", "avatar_url", "xp_points", "level", "created_at"]
        read_only_fields = ["id", "level", "created_at", "xp_points"]

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["nickname", "full_name", "avatar_url"]
