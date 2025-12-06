from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from .models import BlockedIP, APIToken, TokenAccessLog, AttackLog
from .utils import rate_limit_check, telegram_alert
import traceback

class RateLimitAndIPBlockMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = self.get_client_ip(request)

        # 1) блокировка по IP
        blocked = BlockedIP.objects.filter(ip=ip).first()
        if blocked and blocked.is_active():
            return JsonResponse({"error": "Your IP is blocked"}, status=403)

        # 2) rate limit по IP (берём конфиг из settings)
        rl_cfg = getattr(settings, "API_RATE_LIMIT", {}).get("IP", {"per_minute": 60, "burst": 5})
        allowed, remaining = rate_limit_check(f"ip:{ip}", rl_cfg["per_minute"], rl_cfg.get("burst", 5))
        if not allowed:
            # лог и блокировка
            AttackLog.objects.create(ip=ip, path=request.path, message="rate limit exceeded")
            telegram_alert(f"Rate limit exceeded for IP {ip} path {request.path}")
            # временно блокируем IP
            BlockedIP.objects.get_or_create(ip=ip, defaults={"reason": "rate-limit", "expires_at": timezone.now() + timezone.timedelta(minutes=10)})
            return JsonResponse({"error": "Too many requests"}, status=429)

        # 3) log token if provided
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        token_obj = None
        if auth.startswith("Bearer "):
            raw_token = auth.split(" ", 1)[1].strip()
            token_obj = APIToken.objects.filter(token=raw_token, is_active=True).first()

        request._sec_token_obj = token_obj
        request._sec_client_ip = ip
        return None

    def process_response(self, request, response):
        try:
            token_obj = getattr(request, "_sec_token_obj", None)
            ip = getattr(request, "_sec_client_ip", self.get_client_ip(request))
            # логируем все API-запросы
            TokenAccessLog.objects.create(
                token=token_obj,
                ip=ip,
                path=(request.path or "")[:250],
                method=request.method,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
                status_code=getattr(response, "status_code", None)
            )
        except Exception:
            traceback.print_exc()
        return response

    @staticmethod
    def get_client_ip(request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR") or ""


from django.utils.deprecation import MiddlewareMixin
from .models import UserSession
from .utils import send_email_notification, send_sms_notification  # функции уведомлений
from django.utils import timezone

class UserSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            session_key = request.session.session_key
            ip = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Проверяем, есть ли активная сессия
            session, created = UserSession.objects.get_or_create(
                user=request.user,
                session_key=session_key,
                defaults={'ip_address': ip, 'user_agent': user_agent}
            )

            # Если сессия новая или с нового устройства
            if created or (session.ip_address != ip or session.user_agent != user_agent):
                # Отправляем уведомление
                send_email_notification(request.user.email, ip, user_agent)
                if hasattr(request.user, 'phone') and request.user.phone:
                    send_sms_notification(request.user.phone, ip, user_agent)

            # Обновляем активную сессию
            session.ip_address = ip
            session.user_agent = user_agent
            session.is_active = True
            session.ended_at = None
            session.save()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
