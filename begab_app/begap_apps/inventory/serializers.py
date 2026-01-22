from rest_framework import serializers
from .models import Branch, Zone, Seat

class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "zone", "number", "icafe_pc_name", "map_x", "map_y", "is_active"]

class ZoneSerializer(serializers.ModelSerializer):
    seats = SeatSerializer(many=True, read_only=True)
    class Meta:
        model = Zone
        fields = ["id", "branch", "name", "type", "price_per_hour", "specs", "seats"]

class BranchSerializer(serializers.ModelSerializer):
    zones = ZoneSerializer(many=True, read_only=True)
    class Meta:
        model = Branch
        fields = [
            "id", "club_id", "name", "address", "description",
            "location", "work_hours", "icafe_api_url", "icafe_auth_token",
            "photos", "zones"
        ]
