from django.contrib import admin
from .models import APIToken, TokenAccessLog, BlockedIP, AttackLog

@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "expires_at")
    search_fields = ("name",)

@admin.register(TokenAccessLog)
class TokenAccessLogAdmin(admin.ModelAdmin):
    list_display = ("token", "ip", "path", "method", "status_code", "created_at")
    list_filter = ("method", "status_code")
    search_fields = ("ip", "path")

@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = ("ip", "reason", "blocked_at", "expires_at")
    search_fields = ("ip",)

@admin.register(AttackLog)
class AttackLogAdmin(admin.ModelAdmin):
    list_display = ("ip", "path", "created_at")
    search_fields = ("ip", "path")

from django.contrib import admin
from .models import UserDeviceLog

@admin.register(UserDeviceLog)
class UserDeviceLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'device', 'browser', 'os', 'ip_address', 'login_time', 'logout_time')
    list_filter = ('browser', 'os', 'device')
    search_fields = ('user__email', 'ip_address', 'device')


# security/admin.py
from django.contrib import admin
from .models import UserSession

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'device', 'browser', 'os', 'ip_address', 'created_at', 'is_active')
    list_filter = ('is_active', 'browser', 'os', 'device')
    search_fields = ('user__email', 'device', 'browser', 'os', 'ip_address')

