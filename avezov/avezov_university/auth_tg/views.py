from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TelegramUser
from .serializers import (
    RegisterSerializer, LoginSerializer, VerifyCodeSerializer,
    ResetPasswordSerializer, VerifyResetCodeSerializer, NewPasswordSerializer
)

import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from .models import TelegramUser
from .telegram import send_code

class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            # Временно для отладки выводим ошибки
            print(serializer.errors)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Генерация кода (метод должен быть в модели TelegramUser)
        code = user.generate_verification_code()

        # Отправка Email
        send_mail(
            "Код подтверждения регистрации",
            f"Ваш код: {code}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )

        return Response({"status": "code_sent"}, status=status.HTTP_200_OK)


class RegisterVerifyCodeAPIView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']

        try:
            user = TelegramUser.objects.get(verification_code=code)
        except TelegramUser.DoesNotExist:
            return Response({"error": "Неверный код"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.code_is_valid(code):
            return Response({"error": "Код истек"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.verification_code = None
        user.code_created_at = None
        user.code_expires_at = None
        user.save()
        return Response({"status": "verified"}, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.utils import timezone
import random
from django.conf import settings
from .models import TelegramUser  # твоя модель
from .serializers import LoginSerializer
from .utils import send_code

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from .models import PendingPassword
from .serializers import LoginSerializer
from .utils import verify_password
from random import randint

class LoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Все поля обязательны'}, status=400)

        try:
            user = TelegramUser.objects.get(email=email)
        except TelegramUser.DoesNotExist:
            return Response({"error": "Неверный email или пароль"}, status=400)

        if not user.check_password(password):
            return Response({"error": "Неверный email или пароль"}, status=400)

        code = user.generate_verification_code()
        send_mail(
            "Код для входа",
            f"Ваш код для входа: {code}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )

        return Response({
            "message": "Код отправлен на email",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }, status=200)

class LoginVerifyCodeAPIView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']

        try:
            user = TelegramUser.objects.get(verification_code=code)
        except TelegramUser.DoesNotExist:
            return Response({"error": "Неверный код"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.code_is_valid(code):
            return Response({"error": "Код истек"}, status=status.HTTP_400_BAD_REQUEST)

        # JWT токены
        refresh = RefreshToken.for_user(user)
        user.verification_code = None
        user.code_created_at = None
        user.code_expires_at = None
        user.save()

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "redirect": "/profile/"
        }, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import TelegramUser
from .serializers import VerifyCodeSerializer
from .telegram import send_code


class VerifyCodeAPIView(APIView):
    """
    Проверка одноразового кода (ТОЛЬКО code)
    """

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]

        try:
            # 🔐 ИЩЕМ ПОЛЬЗОВАТЕЛЯ ПО КОДУ
            user = TelegramUser.objects.get(verification_code=code)
        except TelegramUser.DoesNotExist:
            return Response(
                {"success": False, "error": "Неверный код из email"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ⏳ если есть срок действия
        if user.code_expires_at and user.code_expires_at < timezone.now():
            return Response(
                {"success": False, "error": "Срок действия кода истёк"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ АКТИВАЦИЯ
        user.is_active = True
        user.verification_code = None
        user.code_expires_at = None
        user.save()

        refresh = RefreshToken.for_user(user)

        # 📩 Email уведомление
        if user.email:
            send_mail(
                subject="Успешный вход",
                message="Вы успешно вошли в систему ✅",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

        # 📲 Telegram уведомление
        if user.telegram_id:
            send_code(
                code="Вы успешно вошли в систему ✅",
                action="login_success",
                telegram_id=user.telegram_id
            )

        return Response({
            "success": True,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "redirect": "/profile/"
        }, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TelegramUser
from .telegram_bot import send_code
from django.contrib.auth.hashers import make_password
from .serializers import ResetPasswordSerializer

class ResetPasswordAPIView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]

        user = TelegramUser.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Пользователь не найден"}, status=404)

        if user.is_blocked:
            return Response({"error": "Аккаунт заблокирован"}, status=403)

        if user.code_is_expired():
            return Response({"error": "Код истёк"}, status=400)

        if user.verification_code != code:
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.is_blocked = True
            user.save()
            return Response({"error": "Неверный код"}, status=400)

        user.password = make_password(new_password)
        user.verification_code = ""
        user.failed_attempts = 0
        user.save()

        return Response({"status": "password_changed"}, status=200)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TelegramUser
from .serializers import VerifyResetCodeSerializer

class VerifyResetCodeAPIView(APIView):
    """Проверка кода для сброса пароля через email или Telegram"""
    def post(self, request):
        serializer = VerifyResetCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        telegram_id = serializer.validated_data.get('telegram_id')
        phone = serializer.validated_data.get('phone')
        code = serializer.validated_data['code']

        user = None
        if email:
            user = TelegramUser.objects.filter(email=email).first()
        elif telegram_id:
            user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
        elif phone:
            user = TelegramUser.objects.filter(phone=phone).first()

        if not user:
            return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        if user.reset_code != code:
            return Response({"error": "Неверный код"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_reset_code_valid():
            return Response({"error": "Код истёк"}, status=status.HTTP_400_BAD_REQUEST)

        # Код верный — можно далее менять пароль
        return Response({"status": "reset_code_verified"}, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TelegramUser
from .serializers import NewPasswordSerializer

class NewPasswordAPIView(APIView):
    """Установка нового пароля через email, telegram_id или phone"""
    def post(self, request):
        serializer = NewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        telegram_id = serializer.validated_data.get('telegram_id')
        phone = serializer.validated_data.get('phone')
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        # Ищем пользователя
        user = None
        if email:
            user = TelegramUser.objects.filter(email=email).first()
        elif telegram_id:
            user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
        elif phone:
            user = TelegramUser.objects.filter(phone=phone).first()

        if not user:
            return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Проверка кода
        if user.reset_code != code or not user.is_reset_code_valid():
            return Response({"error": "Неверный или истёкший код"}, status=status.HTTP_400_BAD_REQUEST)

        # Меняем пароль и сбрасываем код
        user.set_password(new_password)
        user.reset_code = None
        user.reset_code_created_at = None
        user.save(update_fields=['password', 'reset_code', 'reset_code_created_at'])

        return Response({"status": "password_updated"}, status=status.HTTP_200_OK)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .serializers import UserProfileSerializer

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")  # берём из URL
        user = get_object_or_404(User, id=user_id)
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    def put(self, request, email):
        try:
            user = TelegramUser.objects.get(email=email)
        except TelegramUser.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            # Проверка аттестации: если не совпадает, возвращаем ошибку
            attestation = serializer.validated_data.get("attestation_doc")
            if attestation:
                # Здесь можно добавить проверку документа (например, через OCR или базу)
                # Если документ не валиден:
                # return Response({"error": "Не ваша аттестация, загрузите свой"}, status=400)
                pass

            serializer.save()
            return Response({"success": "Профиль обновлён", "profile": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

import random
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TelegramUser
from .serializers import ForgotPasswordSerializer
from .telegram_bot import send_code


class ForgotPasswordAPIView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = TelegramUser.objects.filter(email=email).first()

        if not user:
            return Response({"error": "Пользователь не найден"}, status=404)

        if user.is_blocked:
            return Response({"error": "Аккаунт заблокирован"}, status=403)

        code = str(random.randint(100000, 999999))
        user.verification_code = code
        user.code_created_at = timezone.now()
        user.failed_attempts = 0
        user.save()

        send_code(
            code=code,
            action="восстановления пароля",
            email=user.email,
            telegram_id=user.telegram_id
        )

        return Response({"status": "code_sent"}, status=200)

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import ResendCodeSerializer
from .models import VerificationCode  # модель для хранения OTP
import random

User = get_user_model()

class ResendCodeAPIView(APIView):
    """
    Повторная отправка кода на email
    """
    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Генерируем новый 4-значный код
        code = f"{random.randint(1000, 9999)}"

        # Сохраняем код в модели VerificationCode (срок действия 5 минут)
        VerificationCode.objects.update_or_create(
            user=user,
            defaults={"code": code}
        )

        # Отправка кода на email (или Telegram)
        # Здесь пример для email
        user.email_user(
            subject="Ваш код подтверждения",
            message=f"Ваш код: {code}"
        )

        return Response({"message": "Код отправлен повторно"}, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UsersSerializer
import requests

User = get_user_model()

# ---------------- Google Auth ----------------
class GoogleAuthAPIView(APIView):
    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'error': 'ID token required'}, status=400)

        # Проверяем токен у Google
        google_url = f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
        r = requests.get(google_url)
        if r.status_code != 200:
            return Response({'error': 'Invalid token'}, status=400)

        user_info = r.json()
        email = user_info['email']
        google_id = user_info['sub']
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': first_name,
                'last_name': last_name,
            }
        )

        # Создаём JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        })

# ---------------- Profile ----------------
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import UsersSerializer

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsersSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UsersSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

# auth_tg/views.py
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import timedelta
from .models import PasswordResetCode
from django.utils.timezone import now
from datetime import timedelta
from django.core.exceptions import ValidationError
from .utilses.password_validator import validate_password_strength
from .models import PasswordAttempt, PasswordResetCode

User = get_user_model()

class ForgotsPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email required'}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        reset = PasswordResetCode.objects.create(user=user)

        # ⬇️ тут можно отправить email / telegram
        print(f"RESET LINK: http://localhost:3000/reset-password/{reset.code}")

        return Response({'message': 'Reset link sent'})


class ResetsPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        password = request.data.get('password')
        confirm = request.data.get('confirm_password')

        if password != confirm:
            return Response({'error': 'Пароли не совпадают'}, status=400)

        reset = PasswordResetCode.objects.filter(code=code).first()
        if not reset:
            return Response({'error': 'Неверный код'}, status=400)

        user = reset.user

        attempt, _ = PasswordAttempt.objects.get_or_create(user=user)

        if attempt.blocked_until and attempt.blocked_until > now():
            return Response({
                'error': 'Слишком много попыток. Попробуйте позже.'
            }, status=403)

        try:
            validate_password_strength(password)
        except ValidationError as e:
            attempt.attempts += 1

            if attempt.attempts >= 5:
                attempt.blocked_until = now() + timedelta(minutes=10)
                attempt.attempts = 0

            attempt.save()
            return Response({'error': e.messages[0]}, status=400)

        user.set_password(password)
        user.save()

        attempt.attempts = 0
        attempt.blocked_until = None
        attempt.save()

        reset.delete()

        return Response({'message': 'Пароль успешно изменён'})

class ChangesPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm = request.data.get('confirm_password')

        if not user.check_password(old_password):
            return Response({'error': 'Старый пароль неверный'}, status=400)

        if new_password != confirm:
            return Response({'error': 'Пароли не совпадают'}, status=400)

        try:
            validate_password_strength(new_password)
        except ValidationError as e:
            return Response({'error': e.messages[0]}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Пароль изменён'})


from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class ResetPasswordRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"http://localhost:3000/reset-password/{uid}/{token}"

        send_mail(
            'Сброс пароля',
            f'Перейдите по ссылке, чтобы сбросить пароль: {reset_link}',
            'no-reply@example.com',
            [email],
            fail_silently=False,
        )

        return Response({'message': 'Reset link sent to email'})


class ResetPasswordConfirmView(APIView):
    def post(self, request, uid, token):
        password = request.data.get('password')
        if not password:
            return Response({'error': 'Password required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid link'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        return Response({'message': 'Password has been reset successfully'})

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response({'error': 'Неверный текущий пароль'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({'error': 'Пароль слишком короткий'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Пароль успешно изменён'})


from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP, TelegramUser

class SendOTPAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Введите email"}, status=400)

        try:
            user = TelegramUser.objects.get(email=email)
        except TelegramUser.DoesNotExist:
            user = None  # Если пользователя нет, OTP можно создать без привязки

        otp = OTP.objects.create(user=user)  # Убираем email

        send_mail(
            "Код для сброса пароля",
            f"Ваш код: {otp.code}\nОн действителен 5 минут.",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return Response({"message": "Код отправлен на email"}, status=200)

# Подтверждение смены пароля
class ConfirmChangePasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not all([email, code, new_password, confirm_password]):
            return Response({'error': 'Все поля обязательны'}, status=400)

        if new_password != confirm_password:
            return Response({'error': 'Пароли не совпадают'}, status=400)

        try:
            user = TelegramUser.objects.get(email=email)
        except TelegramUser.DoesNotExist:
            return Response({'error': 'Неверный email'}, status=400)

        otp_obj = OTP.objects.filter(user=user, code=code, is_used=False).first()
        if not otp_obj or otp_obj.is_expired():
            return Response({'error': 'Неверный код или код истёк'}, status=400)

        user.set_password(new_password)  # хэширование
        otp_obj.is_used = True
        otp_obj.save()

        return Response({'message': 'Пароль успешно изменён'}, status=200)

class ConfirmLoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        otp_obj = OTP.objects.filter(email=email, code=code, is_used=False).first()
        if not otp_obj:
            return Response({"error": "Неверный код"}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.is_used = True
        otp_obj.save()

        user = User.objects.get(email=email)
        return Response({"status": "login_success", "email": user.email}, status=status.HTTP_200_OK)

# auth_tg/views.py
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .serializers import ChangesPasswordSerializer

class ConfirmedChangePasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        if not all([email, code, new_password]):
            return Response({"error": "Заполните все поля"}, status=400)

        try:
            otp = OTP.objects.get(email=email, code=code, is_used=False)
        except OTP.DoesNotExist:
            return Response({"error": "Неверный код"}, status=400)

        if otp.is_expired():
            return Response({"error": "Код истёк"}, status=400)

        if not otp.user:
            return Response({"error": "Пользователь не найден"}, status=404)

        otp.user.set_password(new_password)
        otp.user.save()

        otp.is_used = True
        otp.save()

        return Response({"message": "Пароль успешно обновлён"}, status=200)

# auth_tg/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.utils import timezone
from .models import TelegramUser, OTP
from .serializers import ForgotPasswordSerializer, ResetsPasswordSerializer
import random

class ForgotssPasswordAPIView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = TelegramUser.objects.get(email=email)
        except TelegramUser.DoesNotExist:
            return Response({"error": "Пользователь с таким email не найден"}, status=400)

        code = f"{random.randint(1000, 9999)}"
        OTP.objects.create(user=user, code=code, expires_at=timezone.now() + timezone.timedelta(minutes=5))

        send_mail(
            "Код для сброса пароля",
            f"Ваш код для сброса пароля: {code}",
            "noreply@example.com",
            [user.email],
            fail_silently=False
        )

        return Response({"message": "Код отправлен на email"}, status=status.HTTP_200_OK)


class ResetdPasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        if not email or not code or not new_password:
            return Response({"error": "Заполните все поля"}, status=400)

        try:
            otp = OTP.objects.get(email=email, code=code, is_used=False)
        except OTP.DoesNotExist:
            return Response({"error": "Неверный код"}, status=400)

        if otp.is_expired():
            return Response({"error": "Код истёк"}, status=400)

        if not otp.user:
            return Response({"error": "Пользователь с таким email не найден"}, status=400)

        otp.user.set_password(new_password)
        otp.user.save()
        otp.is_used = True
        otp.save()

        return Response({"message": "Пароль успешно обновлён"}, status=200)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordResetToken

class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            # Создаем уникальный токен
            token = PasswordResetToken.objects.create(user=user)
            # Формируем ссылку для сброса
            reset_url = f"http://localhost:3000/rest-verify?token={token.token}"
            # Отправка email
            send_mail(
                subject="Сброс пароля",
                message=f"Перейдите по ссылке для сброса пароля:\n{reset_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            # Если пользователя нет, просто "молчим"
            pass

        return Response({"detail": "Ссылка для сброса пароля отправлена на email"})

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import PasswordResetToken

class VerifyPasswordResetView(APIView):
    def post(self, request):
        token_value = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token_value or not new_password:
            return Response({"detail": "Токен и новый пароль обязательны"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reset_token = PasswordResetToken.objects.get(token=token_value, is_used=False)
        except PasswordResetToken.DoesNotExist:
            return Response({"detail": "Неверный или использованный токен"}, status=status.HTTP_400_BAD_REQUEST)

        if reset_token.is_expired():
            return Response({"detail": "Токен истёк"}, status=status.HTTP_400_BAD_REQUEST)

        # Меняем пароль
        user = reset_token.user
        user.set_password(new_password)
        user.save()

        # Отмечаем токен как использованный
        reset_token.is_used = True
        reset_token.save()

        return Response({"detail": "Пароль успешно изменён"}, status=status.HTTP_200_OK)


