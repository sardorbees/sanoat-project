from celery import shared_task
from django.utils import timezone
from .models import TelegramUser
from .telegram_bot import send_redirect_link

@shared_task
def auto_redirect(telegram_id, redirect_url):
    from time import sleep
    sleep(15)  # ждем 15 секунд
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        if not user.is_verified:
            send_redirect_link(telegram_id, redirect_url)
    except TelegramUser.DoesNotExist:
        pass