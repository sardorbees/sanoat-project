from telegram import Bot, Update
from telegram.ext import CommandHandler, Updater
from django.conf import settings
from django.core.mail import send_mail
from .models import TelegramUser
import logging
import requests

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)


def send_code(*, code, action="register", telegram_id=None, email=None):
    """
    Отправка кода одновременно в Telegram и Email (если указаны).
    """
    text = f"Ваш код для {action}: {code}. Действует 40 минут."

    # 🔹 Telegram
    if telegram_id:
        try:
            pass
        except Exception as e:
            logger.error(f"Telegram error: {e}")

    # 🔹 Email
    if email:
        try:
            send_mail(
                subject="Код подтверждения",
                message=text,
                from_email="no-reply@site.com",
                recipient_list=[email],
                fail_silently=True
            )
            logger.info(f"Код {code} отправлен на Email → {email}")
        except Exception as e:
            logger.error(f"Ошибка Email ({email}): {e}")

    if not telegram_id and not email:
        logger.warning("❗ Нет telegram_id и email — код не отправлен")

from telegram.error import TimedOut, TelegramError
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

def send_code_with_fallback(*, telegram_id=None, email=None, code=None, action="login"):
    text = f"Ваш код для {action}: {code}. Действует 40 минут."

    # 1️⃣ Пытаемся Telegram
    if telegram_id:
        try:
            bot.send_message(chat_id=telegram_id, text=text, timeout=10)
            logger.info(f"TG OK → {telegram_id}")
            return True
        except (TimedOut, TelegramError) as e:
            logger.warning(f"TG FAIL → {telegram_id}: {e}")

    # 2️⃣ Email fallback
    if email:
        send_mail(
            subject=f"Код для {action}",
            message=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        logger.info(f"EMAIL OK → {email}")
        return True

    return False


# telegram_bot.py
from telegram import Bot
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

def send_redirect_link(telegram_id, link):
    """Отправка пользователю ссылки для авторизации через Telegram"""
    try:
        bot.send_message(
            chat_id=telegram_id,
            text=f"Для авторизации перейдите по ссылке: {link}"
        )
        logger.info(f"Отправлена redirect-ссылка пользователю {telegram_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке redirect-ссылки пользователю {telegram_id}: {e}")

def send_telegram_code(telegram_id, code):
    if not telegram_id:
        return

    url = f"https://api.telegram.org/bot{settings.TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": f"🔐 Код для восстановления пароля: {code}"
    }
    requests.post(url, json=payload)
