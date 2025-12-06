from django.db import models
from django.conf import settings

class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('text','Text'),
        ('image','Image'),
        ('file','File'),
        ('audio','Audio'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="chat_images/", null=True, blank=True)
    file = models.FileField(upload_to="chat_files/", null=True, blank=True)
    is_sent = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    voice = models.FileField(upload_to="chat_voices/", blank=True, null=True)
    audio = models.FileField(upload_to="chat_audio/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)   # ✔ delivered
    seen = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}: {self.content}: {self.content[:30]}"

class EmailLog(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=(('sent','sent'),('error','error')))
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient} - {self.subject} - {self.status}"


class BlockedUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_info')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Blocked: {self.user.username}"
        return f"Blocked IP: {self.ip_address}"

from django.db import models
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class OnlineStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="online_status")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    is_typing = models.BooleanField(default=False)  # новый флаг "печатает..."

    @property
    def is_online(self):
        return self.last_seen >= timezone.now() - timedelta(seconds=10)

    def last_seen_display(self):
        delta = timezone.now() - self.last_seen
        seconds = delta.total_seconds()

        if seconds < 60:
            return "был только что"
        elif seconds < 3600:
            return f"был {int(seconds // 60)} мин назад"
        else:
            return "давно"

    def __str__(self):
        return f"{self.user.username} — {'Online' if self.is_online else 'Offline'}"

