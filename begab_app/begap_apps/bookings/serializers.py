# bookings/serializers.py
from rest_framework import serializers
from .models import Booking, Branch, Seat

class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "number", "status"]

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"

from rest_framework import serializers
from .models import Booking

class BookingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = (
            'id',
            'service_name',
            'visit_datetime',
            'status',
            'price',
            'penalty_amount',
        )