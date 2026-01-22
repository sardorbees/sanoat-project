from rest_framework import serializers
from .models import Banner, Club

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "image_url", "action_link", "priority", "is_active", "created_at"]

class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ["id", "name", "logo_url", "rating"]
