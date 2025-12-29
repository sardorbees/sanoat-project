from rest_framework import generics, status
from rest_framework.response import Response
import requests

from .models import Application
from .serializers import ApplicationSerializer

# 🔹 Telegram
TELEGRAM_TOKEN = '8437488119:AAFRIacDxPZa7zxySi52IL3c_WeQL0ozWzI'
TELEGRAM_CHAT_ID = '@avezov_university'


class ApplicationCreateView(generics.CreateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer

    def create(self, request, *args, **kwargs):
        phone = request.data.get('phone_number')
        email = request.data.get('email')

        # ❗ хотя бы одно поле обязательно
        if not phone and not email:
            return Response(
                {"detail": "Укажите хотя бы телефон или email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ❌ НЕТ проверок по времени
        # ❌ НЕТ cache
        # ❌ НЕТ блокировок

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        # 🔔 Telegram уведомление
        self.send_telegram_notification(application)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def send_telegram_notification(self, application):
        message = (
            f"📥 Новая заявка на sanoat_xabarlar\n"
            f"👤 Имя: {application.full_name}\n"
            f"📞 Телефон: {application.phone_number or 'не указан'}\n"
            f"📧 Email: {application.email or 'не указан'}\n"
            f"💬 Вопрос: {application.question}\n"
        )

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=5
        )

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def get_csrf(request):
    return JsonResponse({'success': True})