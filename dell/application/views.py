from rest_framework import generics, status
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.cache import cache
from pytz import timezone as django_timezone
import requests

from .models import Application
from .serializers import ApplicationSerializer

# 🔹 Токен и чат ID Telegram
TELEGRAM_TOKEN = '8061451040:AAE_z1MeU0CV_IU9zvTJjqB0SgkebczyWu4'
TELEGRAM_CHAT_ID = '@sanoat_xabarlar'


class ApplicationCreateView(generics.CreateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer

    def create(self, request, *args, **kwargs):
        phone = request.data.get('phone_number')
        email = request.data.get('email')

        if not phone and not email:
            return Response(
                {"detail": "Укажите хотя бы телефон или email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if phone:
            redis_key = f'form_block_phone_{phone}'
            if cache.get(redis_key):
                return Response(
                    {"detail": "Вы уже отправляли заявку. Повторите через 2 минуты."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            if Application.objects.filter(
                phone_number=phone,
                created_at__gte=timezone.now() - timedelta(minutes=2)
            ).exists():
                return Response(
                    {"detail": "С этого номера уже отправляли заявку. Повторите через 2 минуты."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

        if email:
            redis_key_email = f'form_block_email_{email}'
            if cache.get(redis_key_email):
                return Response(
                    {"detail": "Вы уже отправляли заявку с этим email. Повторите через 2 минуты."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            if Application.objects.filter(
                email=email,
                created_at__gte=timezone.now() - timedelta(minutes=5)
            ).exists():
                return Response(
                    {"detail": "С этим email уже отправляли заявку. Повторите через 2 минуты."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        if phone:
            cache.set(f'form_block_phone_{phone}', '1', timeout=60 * 5)
        if email:
            cache.set(f'form_block_email_{email}', '1', timeout=60 * 5)

        self.send_telegram_notification(application)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def send_telegram_notification(self, application):
        uz_time = datetime.now(django_timezone('Asia/Tashkent'))
        if 9 <= uz_time.hour <= 20:
            message = (
                f"📥 Новая заявка на sanoat_xabarlar\n"
                f"👤 Имя: {application.full_name}\n"
                f"📞 Телефон: {application.phone_number or 'не указан'}\n"
                f"📧 Email: {application.email or 'не указан'}\n"
                f"💬 Вопрос: {application.question}\n"
            )
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
