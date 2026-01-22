# app/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Level(models.Model):
    name = models.CharField(max_length=50)
    xp_required = models.PositiveIntegerField()

    class Meta:
        ordering = ["xp_required"]

    def __str__(self):
        return f"{self.name} ({self.xp_required} XP)"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    xp = models.PositiveIntegerField(default=0)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.user.username


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    completed = models.BooleanField(default=False)

    def duration_hours(self):
        delta = self.end_time - self.start_time
        return max(delta.total_seconds() / 3600, 0)
