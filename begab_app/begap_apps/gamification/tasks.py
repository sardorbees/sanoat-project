# app/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from .models import Booking, UserProfile, Level


@shared_task
def process_completed_bookings():
    now = timezone.now()

    bookings = Booking.objects.filter(
        end_time__lte=now,
        completed=False
    )

    for booking in bookings:
        with transaction.atomic():
            profile, _ = UserProfile.objects.get_or_create(user=booking.user)

            hours = booking.duration_hours()
            gained_xp = int(hours * 10)

            profile.xp += gained_xp

            # Level Up check
            next_level = (
                Level.objects
                .filter(xp_required__lte=profile.xp)
                .order_by("-xp_required")
                .first()
            )

            if next_level and profile.level != next_level:
                profile.level = next_level
                send_level_up_push.delay(profile.user.id)

            profile.save()

            booking.completed = True
            booking.save()
