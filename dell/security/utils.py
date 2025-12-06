import redis
import requests
import secrets
import time
from datetime import timedelta, datetime, timezone
from django.conf import settings

# Redis client (использует REDIS_URL в settings)
REDIS_URL = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")
redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

# Telegram alert helper
def telegram_alert(text: str):
    bot = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat = getattr(settings, "TELEGRAM_CHAT_ID", None)
    if not bot or not chat:
        return False
    url = f"https://api.telegram.org/bot{bot}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat, "text": text}, timeout=5)
        return True
    except requests.RequestException:
        return False

def generate_strong_token(nbytes=32):
    return secrets.token_urlsafe(nbytes)

def rate_limit_check(key: str, max_per_minute: int, burst: int = 5):
    now = int(time.time())
    window_key = f"rl:{key}:{now // 60}"
    p = redis_client.pipeline()
    p.incr(window_key, 1)
    p.expire(window_key, 65)
    val, _ = p.execute()
    allowed = val <= (max_per_minute + burst)
    remaining = max(0, max_per_minute + burst - val)
    return allowed, int(remaining)


from django.core.mail import send_mail
from django.conf import settings

def send_email_notification(email, ip, user_agent):
    subject = "Новый вход в ваш аккаунт"
    message = f"""
    <b>Новый вход в аккаунт</b>
    Пользователь: {user.first_name or user.email}
    Username: {user.username}
    IP: {ip}
    Устройство: {device}  # например: Мобильный, Планшет, ПК
    ОС: {os_name}          # например: Windows 10, Android 13
    Браузер: {browser}     # например: Chrome, Yandex Browser
    Время: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

    Если это были вы — ничего делать не нужно.
    Если нет — срочно смените пароль!
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

def send_sms_notification(phone, ip, user_agent):
    # Здесь можно использовать ваш SMS-провайдер
    message = f"Новый вход: IP={ip}, Device={user_agent}"
    # Пример вызова функции send_sms(phone, message)
    from phone.utils import send_sms
    send_sms(phone, message)


# security/utils.py
import httpagentparser


def parse_user_agent(user_agent):
    parsed = httpagentparser.detect(user_agent)

    browser = parsed.get('browser', {}).get('name', 'Unknown')
    os = parsed.get('platform', {}).get('name', 'Unknown')
    device = parsed.get('dist', {}).get('name', 'Unknown')  # ноутбук/ПК/мобильный

    return browser, os, device


# security/utils.py
from user_agents import parse

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def parse_user_agent(user_agent):
    ua = parse(user_agent)

    # Определяем устройство
    if ua.is_mobile:
        device_type = "Мобильный"
    elif ua.is_tablet:
        device_type = "Планшет"
    elif ua.is_pc:
        device_type = "ПК"
    else:
        device_type = "Другое"

    # Более точная марка/модель (если возможно)
    device_brand = ua.device.brand or "Unknown"
    device_model = ua.device.model or "Unknown"

    device_full = f"{device_brand} {device_model}".strip()
    if device_full == "Unknown Unknown":
        device_full = device_type

    browser = f"{ua.browser.family} {ua.browser.version_string}"
    os_name = f"{ua.os.family} {ua.os.version_string}"

    return browser, os_name, device_full

from django.core.mail import send_mail
from django.utils.html import format_html

def send_pretty_email(to_email, subject, message):
    send_mail(
        subject=subject,
        message='',
        html_message=message,
        from_email='admin@gmail.com',
        recipient_list=[to_email],
        fail_silently=False,
    )

# security/middleware.py
from django.http import HttpResponseForbidden

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # здесь можно проверять IP, лимит запросов
        response = self.get_response(request)
        return response

