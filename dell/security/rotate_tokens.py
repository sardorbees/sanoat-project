from django.core.management.base import BaseCommand
from security.models import APIToken
from security.utils import generate_strong_token
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = "Rotate API tokens"

    def handle(self, *args, **options):
        rotation_days = getattr(__import__("django.conf").conf.settings, "API_TOKEN_ROTATION_DAYS", 1)
        for token in APIToken.objects.filter(is_active=True):
            new_value = generate_strong_token(32)
            token.is_active = False
            token.save()
            APIToken.objects.create(
                name=f"{token.name}-rotated-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                token=new_value,
                created_at=timezone.now(),
                expires_at=timezone.now() + timedelta(days=rotation_days),
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f"Rotated {token.name}"))
