# app/serializers.py
from rest_framework import serializers
from .models import UserProfile, Level


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = "__all__"


class UserProfileSerializer(serializers.ModelSerializer):
    level = LevelSerializer()

    class Meta:
        model = UserProfile
        fields = ("xp", "level")
