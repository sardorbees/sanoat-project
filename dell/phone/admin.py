from django.contrib import admin
from .models import PhoneOTP

@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "created_at", "is_verified")
    list_filter = ("is_verified",)
