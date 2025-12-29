from telegram import Bot
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)


def send_code(*, telegram_id=None, email=None, code=None, action="register"):
    text = f"Ваш код для {action}: {code}. Действует 40 минут."

    if telegram_id:
        try:
            bot.send_message(chat_id=telegram_id, text=text)
            logger.info(f"Код {code} отправлен в Telegram {telegram_id}")
        except Exception as e:
            logger.error(f"Telegram error {telegram_id}: {e}")

    if email:
        try:
            send_mail(
                subject=f"Код для {action}",
                message=text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )
            logger.info(f"Код {code} отправлен на email {email}")
        except Exception as e:
            logger.error(f"Email error {email}: {e}")


import uuid
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from .models import TelegramAuthCode

def create_telegram_auth_link(phone, first_name='', last_name=''):
    # Создаём пользователя или получаем существующего
    user, _ = User.objects.get_or_create(
        username=phone,
        defaults={'first_name': first_name, 'last_name': last_name}
    )

    # Генерируем уникальный код
    code = uuid.uuid4().hex
    expires_at = timezone.now() + timedelta(minutes=10)

    TelegramAuthCode.objects.create(
        user=user,
        phone=phone,
        code=code,
        expires_at=expires_at
    )

    return code, user

from django.core.mail import send_mail

def send_email_code(email, code):
    send_mail(
        subject='Код подтверждения смены пароля',
        message=f'Ваш код подтверждения: {code}',
        from_email='noreply@site.com',
        recipient_list=[email],
        fail_silently=False,
    )

from django.contrib.auth.hashers import check_password

def verify_password(user, password):
    """
    Проверяет пароль:
    - Старый пароль
    - Новый пароль, если уже подтверждён через OTP
    """
    # Старый пароль
    if check_password(password, user.password):
        return True

    # Новый пароль, который уже был подтверждён
    if hasattr(user, 'pending_password') and user.pending_password.confirmed:
        if check_password(password, user.pending_password.new_password):
            return True

    return False
