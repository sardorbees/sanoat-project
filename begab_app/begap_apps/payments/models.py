import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class PaymentMethod(models.Model):
    METHOD_CHOICES = (
        ('card', 'Card'),
        ('click', 'Click'),
        ('payme', 'Payme'),
        ('wallet', 'Wallet'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    type = models.CharField(max_length=20, choices=METHOD_CHOICES)
    title = models.CharField(max_length=100)
    masked_number = models.CharField(max_length=30, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.title}"
