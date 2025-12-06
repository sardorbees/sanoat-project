from django.db import models
from django.utils import timezone

class APIToken(models.Model):
    name = models.CharField(max_length=100)
    token = models.CharField(max_length=256, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"


class TokenAccessLog(models.Model):
    token = models.ForeignKey(APIToken, null=True, blank=True, on_delete=models.SET_NULL)
    ip = models.CharField(max_length=45)  # IPv6 safe
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    user_agent = models.TextField(blank=True)
    status_code = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class BlockedIP(models.Model):
    ip = models.CharField(max_length=45, unique=True)
    reason = models.CharField(max_length=200, blank=True)
    blocked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def is_active(self):
        if self.expires_at:
            return timezone.now() < self.expires_at
        return True

    def __str__(self):
        return f"{self.ip} ({'active' if self.is_active() else 'expired'})"


class AttackLog(models.Model):
    ip = models.CharField(max_length=45)
    path = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

from django.db import models
from django.conf import settings
from django.utils import timezone

class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.device} - {self.browser} ({'активна' if self.is_active else 'завершена'})"





from django.db import models
from django.conf import settings

class UserDeviceLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    browser = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    device = models.CharField(max_length=100)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.device} - {self.browser} - {self.ip_address}"
