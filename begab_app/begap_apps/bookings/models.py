# bookings/models.py
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

class Branch(models.Model):
    name = models.CharField(max_length=255)

class Seat(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="seats")
    number = models.CharField(max_length=10)
    STATUS_CHOICES = [
        ("FREE", "Free"),
        ("MAINTENANCE", "Maintenance"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="FREE")

class Booking(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        SYNCED = "SYNCED", "Synced"
        ACTIVE = "ACTIVE", "Active"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_name = models.CharField(max_length=255, null=True, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name="bookings", null=True, blank=True)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    penalty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    icafe_session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visit_datetime = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ("seat", "start_time", "end_time")

    # --------------------
    # БИЗНЕС-ЛОГИКА
    # --------------------

    def can_cancel(self) -> bool:
        """
        Отмена разрешена:
        - если бронирование не завершено
        - если до start_time больше 30 минут
        """
        if self.status in [self.Status.CANCELLED, self.Status.COMPLETED]:
            return False

        return self.start_time - timezone.now() > timezone.timedelta(minutes=30)

    def calculate_penalty(self) -> Decimal:
        """
        Штраф:
        - если меньше 30 минут → 30%
        """
        return self.total_amount * Decimal("0.30")

    def __str__(self):
        return f"Booking {self.id} ({self.status})"
