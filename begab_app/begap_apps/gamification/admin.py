# app/admin.py
from django.contrib import admin
from .models import Level, UserProfile, Booking


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("name", "xp_required")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "xp", "level")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("user", "start_time", "end_time", "completed")
