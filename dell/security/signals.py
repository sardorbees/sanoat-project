from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from .models import UserSession
from django.utils import timezone

@receiver(user_logged_out)
def end_user_session(sender, request, user, **kwargs):
    session_key = request.session.session_key
    try:
        session = UserSession.objects.get(user=user, session_key=session_key, is_active=True)
        session.is_active = False
        session.ended_at = timezone.now()
        session.save()
    except UserSession.DoesNotExist:
        pass


from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models import UserDeviceLog
from user_agents import parse


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = parse(ua_string)

    UserDeviceLog.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=ua_string,
        browser=f"{user_agent.browser.family} {user_agent.browser.version_string}",
        os=f"{user_agent.os.family} {user_agent.os.version_string}",
        device=f"{user_agent.device.family} {user_agent.device.brand or ''} {user_agent.device.model or ''}"
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    # Находим последнюю запись без logout_time
    try:
        log = UserDeviceLog.objects.filter(user=user, ip_address=ip, logout_time__isnull=True).latest('login_time')
        log.logout_time = timezone.now()
        log.save()
    except UserDeviceLog.DoesNotExist:
        pass


# security/signals.py
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import UserSession
from .utils import parse_user_agent, get_client_ip
from .notifications import send_telegram_message, send_sms

# ---- Вход ----
@receiver(user_logged_in)
def create_user_session(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    browser, os_name, device = parse_user_agent(user_agent)

    session_key = request.session.session_key or request.session.create()

    # Создаем запись о сессии
    UserSession.objects.create(
        user=user,
        session_key=session_key,
        ip_address=ip,
        user_agent=user_agent,
        browser=browser,
        os=os_name,
        device=device
    )

    text = f"""
    <b>Вход в аккаунт</b>
    Пользователь: {user.first_name or user.email}
    Username: {user.username}
    IP: {ip}
    Устройство: {device}
    ОС: {os_name}
    Браузер: {browser}
    Время: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
    """

    try:
        send_mail("Вход в аккаунт", text, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as e:
        print("Email send error:", e)

    try:
        send_telegram_message(text)
    except Exception as e:
        print("Telegram send error:", e)

    try:
        if user.phone_number:
            send_sms(user.phone_number, f"Вход в аккаунт с IP {ip}, устройство: {device}, время: {timezone.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print("SMS send error:", e)


# ---- Выход ----
@receiver(user_logged_out)
def end_user_session(sender, request, user, **kwargs):
    session_key = request.session.session_key
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    browser, os_name, device = parse_user_agent(user_agent)

    # Находим активную сессию
    try:
        session = UserSession.objects.get(user=user, session_key=session_key, is_active=True)
        session.ended_at = timezone.now()
        session.is_active = False
        session.save()
    except UserSession.DoesNotExist:
        session = None

    text = f"""
<b>Выход из аккаунта</b>
Пользователь: {user.first_name or user.email}
IP: {ip}
Устройство: {device}
ОС: {os_name}
Браузер: {browser}
Время: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    try:
        send_mail("Выход из аккаунта", text, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as e:
        print("Email send error:", e)

    try:
        send_telegram_message(text)
    except Exception as e:
        print("Telegram send error:", e)

    try:
        if user.phone_number:
            send_sms(user.phone_number, f"Выход из аккаунта с IP {ip}, устройство: {device}, время: {timezone.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print("SMS send error:", e)