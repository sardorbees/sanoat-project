from django.db import models
from django.utils import timezone
from datetime import timedelta

class PhoneOTP(models.Model):
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def can_resend(self):
        return timezone.now() > self.created_at + timedelta(seconds=60)

    def __str__(self):
        return f"{self.phone} - {self.code}"
