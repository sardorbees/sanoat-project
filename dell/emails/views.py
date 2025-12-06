from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, EmailVerification
from .serializers import SendCodeSerializer, VerifyCodeSerializer
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from .models import User, EmailVerification
from .serializers import SendCodeSerializer
from django.conf import settings

class SendCodeView(APIView):
    def post(self, request):
        serializer = SendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        # Создаём пользователя или получаем существующего
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": email.split("@")[0]}
        )

        # Создаём объект EmailVerification или получаем существующий
        verify_obj, created = EmailVerification.objects.get_or_create(user=user)
        code = verify_obj.generate_code()

        # 🔹 Красивое HTML письмо
        subject = "Ваш код подтверждения"
        from_email = settings.DEFAULT_FROM_EMAIL  # или "no-reply@example.com"
        to = [email]

        text_content = f"Ваш код: {code}"  # текстовая версия на случай, если email клиент не поддерживает HTML

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
              <h2 style="color: #333;">Код подтверждения</h2>
              <p>Ваш код для подтверждения: <strong style="font-size: 24px; color: #1a73e8;">{code}</strong></p>
              <p>Срок действия кода: <strong>5 минут</strong></p>
              <hr>
              <p style="font-size: 12px; color: #888;">Если вы не запрашивали код, просто проигнорируйте это письмо.</p>
            </div>
          </body>
        </html>
        """

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        # Postman тест: возвращаем код в JSON (не для продакшена!)
        return Response({
            "message": "Код отправлен на Email",
            "code": code
        })


from django.utils.html import format_html

class VerifyCodeView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # Проверка пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Проверка кода
        try:
            verify_obj = EmailVerification.objects.get(user=user)
        except EmailVerification.DoesNotExist:
            return Response({"error": "Код не найден"}, status=404)

        # Неверный код
        if verify_obj.code != code:
            return Response({"error": "Неверный код"}, status=400)

        # Подтверждаем email
        user.is_verified = True
        user.save()

        # Генерируем JWT-токены
        token = RefreshToken.for_user(user)

        # Красивое письмо подтверждения
        subject = "Ваш Email успешно подтверждён"
        message = format_html(
            """
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #2e7d32;">Email подтверждён</h2>
                <p>Здравствуйте, <b>{name}</b>!</p>

                <p>Ваш email был успешно подтверждён. Теперь вы можете полностью использовать свой профиль и входить в систему без ограничений.</p>

                <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">

                <p style="color: #555;">
                    Если вы не запрашивали подтверждение — просто проигнорируйте это письмо.
                </p>
            </div>
            """,
            name=user.first_name or user.email
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Email подтверждён",
            "access": str(token.access_token),
            "refresh": str(token)
        })


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from .models import User, EmailVerification, ResetPasswordCode
from .serializers import *
from django.conf import settings
import random

def generate_code():
    return str(random.randint(100000, 999999))

# Регистрация
from django.utils.html import format_html
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.utils.crypto import get_random_string
from django.utils.html import format_html

from django.utils.crypto import get_random_string
from django.utils.html import format_html
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, EmailVerification
from .serializers import RegisterSerializer
from .crypto import encrypt_text

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        username = serializer.validated_data['username']

        # Создание пользователя
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': username}
        )

        if not created:
            return Response({"error": "Пользователь уже существует"}, status=400)

        # Генерация временного пароля
        temp_password = get_random_string(10)
        user.set_password(temp_password)

        # Шифруем email перед сохранением (например, в поле email_encrypted)
        user.email_encrypted = encrypt_text(email)
        user.save()

        # Генерация и шифрование кода подтверждения
        verify_obj, _ = EmailVerification.objects.get_or_create(user=user)
        code = verify_obj.generate_code()  # например 6 цифр
        verify_obj.code_encrypted = encrypt_text(code)
        verify_obj.save()

        # Отправка кода по email (расшифровка здесь не нужна, т.к. для пользователя)
        subject = "Код подтверждения email"
        message = format_html(
            """
            <h2>Подтверждение регистрации</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Ваш код подтверждения:</p>

            <h3 style="font-size:26px; font-weight:bold; letter-spacing:3px; margin:20px 0;">{code}</h3>

            <p>Код действует <b>30 секунд</b>.</p>
            <p>Не сообщайте его никому.</p>
            """,
            name=user.username or user.email,
            code=code
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Пользователь создан. Код подтверждения отправлен на email.",
            "redirect": "verify"
        }, status=201)


# Подтверждение email
from django.utils.html import format_html
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, EmailVerification
from .serializers import VerifyCodeSerializer
from .crypto import decrypt_text
from .emails import send_pretty_email

# Логин
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import LoginSerializer


from django.utils.html import format_html
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from django.utils.html import format_html
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.html import format_html
from .utils import send_pretty_email
from .models import User
from .serializers import LoginSerializer

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Email или пароль неверный"}, status=401)

        encrypted_email = User(email_encrypted=None).set_email(email)
        user = authenticate(request, email=email, password=password)

        # --- админ создаёт сразу verified ---
        if not user.is_verified:
            return Response({"error": "Ваш email не подтверждён"}, status=403)

        # ---- Авторизация ----
        user = authenticate(request, email=email, password=password)

        if not user:
            return Response({"error": "Email или пароль неверный"}, status=401)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login успешен",
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })
# Профиль
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

# Сброс пароля
from django.utils.html import format_html
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, ResetPasswordCode
from .serializers import ResetPasswordEmailSerializer
from .emails import send_pretty_email
from .utils import generate_code

MAX_ATTEMPTS = 3

class ResetPasswordSendCodeView(APIView):
    def post(self, request):
        serializer = ResetPasswordEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        # Проверяем, существует ли пользователь
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Генерируем код и шифруем его при сохранении
        code = generate_code()
        reset_obj = ResetPasswordCode.objects.create(user=user)
        reset_obj.code = code
        reset_obj.save()

        # Красивое письмо
        subject = "Код для сброса пароля"
        message = format_html(
            """
            <h2>Сброс пароля</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Вы запросили сброс пароля. Ваш код подтверждения:</p>
            <h3 style="font-size: 24px; letter-spacing: 2px; margin: 15px 0;">{code}</h3>
            <p>Код действует <b>30 секунд</b>. Пожалуйста, используйте его как можно скорее.</p>
            <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
            """,
            name=user.first_name or user.email,
            code=code
        )

        send_pretty_email(email, subject, message)

        return Response({"message": "Код отправлен на email"})



from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.html import format_html
from .models import User, ResetPasswordCode
from .serializers import ResetPasswordVerifyCodeSerializer
from .emails import send_pretty_email
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.html import format_html
from django.utils import timezone
from .models import ResetPasswordCode, User
from .emails import send_pretty_email  # твоя функция отправки писем
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, EmailVerification
from .serializers import SendCodeSerializer, VerifyCodeSerializer
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from .models import User, EmailVerification
from .serializers import SendCodeSerializer
from django.conf import settings

class SendCodeView(APIView):
    def post(self, request):
        serializer = SendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        # Создаём пользователя или получаем существующего
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": email.split("@")[0]}
        )

        # Создаём объект EmailVerification или получаем существующий
        verify_obj, created = EmailVerification.objects.get_or_create(user=user)
        code = verify_obj.generate_code()

        # 🔹 Красивое HTML письмо
        subject = "Ваш код подтверждения"
        from_email = settings.DEFAULT_FROM_EMAIL  # или "no-reply@example.com"
        to = [email]

        text_content = f"Ваш код: {code}"  # текстовая версия на случай, если email клиент не поддерживает HTML

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
              <h2 style="color: #333;">Код подтверждения</h2>
              <p>Ваш код для подтверждения: <strong style="font-size: 24px; color: #1a73e8;">{code}</strong></p>
              <p>Срок действия кода: <strong>5 минут</strong></p>
              <hr>
              <p style="font-size: 12px; color: #888;">Если вы не запрашивали код, просто проигнорируйте это письмо.</p>
            </div>
          </body>
        </html>
        """

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        # Postman тест: возвращаем код в JSON (не для продакшена!)
        return Response({
            "message": "Код отправлен на Email",
            "code": code
        })


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta

from .models import EmailVerification, User
from .serializers import VerifyCodeSerializer
from .emails import send_pretty_email

MAX_ATTEMPTS = 3
CODE_EXPIRE_SECONDS = 180  # 3 минуты

class VerifyCodeView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # Проверяем пользователя и код
        try:
            user = User.objects.get(email=email)
            verify_obj = EmailVerification.objects.get(user=user)
        except (User.DoesNotExist, EmailVerification.DoesNotExist):
            return Response({"error": "Пользователь или код не найден"}, status=404)

        # Проверка срока действия кода
        if timezone.now() > verify_obj.created_at + timedelta(seconds=CODE_EXPIRE_SECONDS):
            return Response({"error": "Срок действия кода истёк. Запросите новый код."}, status=400)

        # Проверка количества попыток
        if verify_obj.attempts >= MAX_ATTEMPTS:
            return Response({"error": "Превышено количество попыток. Попробуйте через 4 минуты."}, status=400)

        # Проверка кода
        if verify_obj.code != code:
            verify_obj.attempts += 1
            verify_obj.save()
            return Response(
                {"error": f"Неверный код. Попытка {verify_obj.attempts}/{MAX_ATTEMPTS}"},
                status=400
            )

        # Подтверждение email
        user.is_verified = True
        user.save()

        # Отмечаем код как использованный
        verify_obj.is_used = True
        verify_obj.save()

        # Генерация токена
        token = RefreshToken.for_user(user)

        # Красивое HTML-письмо
        subject = "Ваш Email успешно подтверждён"
        message = format_html(
            """
            <h2>Email подтверждён</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Ваш email был успешно подтверждён. Теперь вы можете пользоваться всеми возможностями системы.</p>
            <p>Спасибо, что вы с нами!</p>
            <hr>
            <p>Если вы не запрашивали подтверждение — просто проигнорируйте это письмо.</p>
            """,
            name=user.first_name or user.email
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Email подтверждён",
            "access": str(token.access_token),
            "refresh": str(token)
        })

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from .models import User, EmailVerification, ResetPasswordCode
from .serializers import *
from django.conf import settings
import random

def generate_code():
    return str(random.randint(100000, 999999))

# Регистрация
from django.utils.html import format_html
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.utils.crypto import get_random_string
from django.utils.html import format_html

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        username = serializer.validated_data['username']

        # Создание пользователя
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': username}
        )

        if not created:
            return Response({"error": "Пользователь уже существует"}, status=400)

        # Генерация временного пароля (не отправляем)
        temp_password = get_random_string(10)
        user.set_password(temp_password)
        user.save()

        # Генерация и отправка кода подтверждения (только цифры)
        verify_obj, _ = EmailVerification.objects.get_or_create(user=user)

        code = verify_obj.generate_code()  # например 6 цифр

        subject = "Код подтверждения email"
        message = format_html(
            """
            <h2>Подтверждение регистрации</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Ваш код подтверждения:</p>

            <h3 style="
                font-size: 26px;
                font-weight: bold;
                letter-spacing: 3px;
                margin: 20px 0;
            ">{code}</h3>

            <p>Код действует <b>30 секунд</b>.</p>
            <p>Не сообщайте его никому.</p>
            """,
            name=user.username or user.email,
            code=code
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Пользователь создан. Код подтверждения отправлен на email.",
            "redirect": "verify"
        }, status=201)



# Подтверждение email
from django.utils.html import format_html

class VerifyCodeView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # Проверяем пользователя и код
        try:
            user = User.objects.get(email=email)
            verify_obj = EmailVerification.objects.get(user=user)
        except (User.DoesNotExist, EmailVerification.DoesNotExist):
            return Response({"error": "Пользователь или код не найден"}, status=404)

        # Неверный код
        if verify_obj.code != code:
            return Response({"error": "Неверный код"}, status=400)

        # Подтверждение email
        user.is_verified = True
        user.save()

        # Генерация токена
        token = RefreshToken.for_user(user)

        # Красивое HTML-письмо
        subject = "Ваш Email успешно подтверждён"
        message = format_html(
            """
            <h2>Email подтверждён</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Ваш email был успешно подтверждён. Теперь вы можете пользоваться всеми возможностями системы.</p>
            <p>Спасибо, что вы с нами!</p>
            <hr>
            <p>Если вы не запрашивали подтверждение — просто проигнорируйте это письмо.</p>
            """,
            name=user.first_name or user.email
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Email подтверждён",
            "access": str(token.access_token),
            "refresh": str(token)
        })


# Логин
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import LoginSerializer


from django.utils.html import format_html
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from django.utils.html import format_html
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        # Проверяем авторизацию
        user = authenticate(request, email=email, password=password)

        if not user:
            return Response({"error": "Email или пароль неверный"}, status=status.HTTP_401_UNAUTHORIZED)

        # Генерируем токены
        refresh = RefreshToken.for_user(user)

        # Красивое HTML-письмо
        subject = "Успешный вход в аккаунт"
        message = format_html(
            """
            <h2>Вход выполнен успешно</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Вы успешно вошли в свой аккаунт. Если это были вы — никаких действий не требуется.</p>
            <p>Если вы НЕ выполняли вход, немедленно измените пароль!</p>
            <hr>
            <p>Дата и время входа: <b>{datetime}</b></p>
            """,
            name=user.first_name or user.email,
            datetime=timezone.now().strftime("%d.%m.%Y %H:%M:%S")
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Login успешен",
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })




# Профиль
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

# Сброс пароля
from django.utils.html import format_html

class ResetPasswordSendCodeView(APIView):
    def post(self, request):
        serializer = ResetPasswordEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        # Проверяем, существует ли пользователь
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Генерируем код
        code = generate_code()
        ResetPasswordCode.objects.create(user=user, code=code)

        # Красивое письмо
        subject = "Код для сброса пароля"
        message = format_html(
            """
            <h2>Сброс пароля</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Вы запросили сброс пароля. Ваш код подтверждения:</p>
            <h3 style="font-size: 24px; letter-spacing: 2px; margin: 15px 0;">{code}</h3>
            <p>Код действует <b>30 секунд</b>. Пожалуйста, используйте его как можно скорее.</p>
            <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
            """,
            name=user.first_name or user.email,
            code=code
        )

        send_pretty_email(email, subject, message)

        return Response({"message": "Код отправлен на email"})


from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.html import format_html
from django.core.exceptions import ObjectDoesNotExist

class ResetPasswordVerifyCodeView(APIView):
    def post(self, request):
        serializer = ResetPasswordVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # Проверка существования пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Получаем последний неиспользованный код
        reset_code = ResetPasswordCode.objects.filter(user=user, is_used=False).order_by('-created_at').first()

        if not reset_code or reset_code.is_expired():
            return Response({"error": "Код не найден или истёк"}, status=400)

        if reset_code.code != code:
            reset_code.attempts += 1
            reset_code.save()
            return Response({"error": "Неверный код"}, status=400)

        # Отмечаем код как использованный
        reset_code.is_used = True
        reset_code.save()

        # Красивое HTML-письмо о подтверждении кода
        subject = "Код подтверждён"
        message = format_html(
            """
            <h2>Код успешно подтверждён</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Ваш код для сброса пароля успешно подтверждён.</p>
            <p>Теперь вы можете установить новый пароль для входа в систему.</p>
            """,
            name=user.first_name or user.email
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Код подтверждён. Письмо с уведомлением отправлено на email."
        })


from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.html import format_html
from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist

class SetNewPasswordView(APIView):
    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']

        # Проверка существования пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Установка нового пароля и вход пользователя
        user.set_password(new_password)
        user.save()
        login(request, user)

        # Красивое HTML-письмо о смене пароля
        subject = "Пароль успешно изменён"
        message = format_html(
            """
            <h2>Пароль обновлён</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Ваш пароль был успешно изменён. Теперь вы можете войти в систему с новым паролем.</p>
            <p>Если это были не вы, немедленно смените пароль или свяжитесь с поддержкой.</p>
            """,
            name=user.first_name or user.email
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Пароль успешно изменён и отправлено уведомление на email.",
            "redirect": "profile"
        })



import random
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import login
from .models import User, ResetPasswordCode
from .serializers import (
    ResetPasswordEmailSerializer,
    ResetPasswordVerifyCodeSerializer,
    SetNewPasswordSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import *
from .models import ResetPasswordCode
from .utils import send_pretty_email
import random
from django.contrib.auth.hashers import make_password

User = get_user_model()


def generate_code():
    return str(random.randint(100000, 999999))

def generate_new_password():
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    return "".join(random.choice(chars) for _ in range(10))

from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.html import format_html
from django.core.exceptions import ObjectDoesNotExist

class ResetPasswordSendCodeView(APIView):
    def post(self, request):
        serializer = ResetPasswordEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        # Проверка существования пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Генерация кода для сброса пароля
        code = generate_code()
        ResetPasswordCode.objects.create(user=user, code=code)

        # Красивое HTML-письмо
        subject = "Код для сброса пароля"
        message = format_html(
            """
            <h2>Сброс пароля</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Вы запросили сброс пароля. Используйте следующий код для подтверждения:</p>
            <h3 style="color: #2E86C1;">{code}</h3>
            <p>Код действителен в течение 30 секунд.</p>
            <p>Если это были не вы, просто проигнорируйте это письмо.</p>
            """,
            name=user.first_name or user.email,
            code=code
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Код подтверждения отправлен на email.",
        })



from django.contrib.auth.hashers import make_password
from django.utils.html import format_html
from rest_framework.response import Response
from rest_framework.views import APIView

class ResetPasswordVerifyView(APIView):
    def post(self, request):
        serializer = ResetPasswordVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # Проверка существования пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Получаем последний код сброса
        try:
            verify = ResetPasswordCode.objects.filter(user=user).latest("created_at")
        except ResetPasswordCode.DoesNotExist:
            return Response({"error": "Код не найден"}, status=404)

        # Проверка срока действия кода
        if verify.is_expired():
            return Response({"error": "Код истёк"}, status=400)

        # Проверка совпадения кода
        if verify.code != code:
            return Response({"error": "Неверный код"}, status=400)

        # Генерация нового пароля и сохранение
        new_password = generate_new_password()
        user.password = make_password(new_password)
        user.save()

        # Красивое HTML-письмо
        subject = "Ваш новый пароль"
        message = format_html(
            """
            <h2>Пароль успешно обновлён</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Ваш новый пароль: <b>{password}</b></p>
            <p>Пожалуйста, сохраните его в надёжном месте.</p>
            """,
            name=user.first_name or user.email,
            password=new_password
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Пароль обновлён. Новый пароль отправлен на email.",
            "redirect": "login"
        })



class SetNewPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        try:
            verify_obj = EmailVerification.objects.get(user=user)
        except EmailVerification.DoesNotExist:
            return Response({"error": "Код для сброса не найден"}, status=404)

        if verify_obj.code != code:
            return Response({"error": "Неверный код"}, status=400)

        user.set_password(new_password)
        user.save()

        # Удаляем код после успешного сброса
        verify_obj.delete()

        return Response({"message": "Пароль успешно изменён"})


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .models import User, EmailCode
from .serializers import *

from django.utils.html import format_html
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist

class VerifyRegisterCodeView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        # Проверка существования пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Проверка кода подтверждения
        try:
            code_obj = EmailCode.objects.get(user=user, code=code, is_used=False)
        except EmailCode.DoesNotExist:
            return Response({"error": "Неверный или уже использованный код"}, status=400)

        if not code_obj.is_valid():
            return Response({"error": "Код истёк или уже использован"}, status=400)

        # Отмечаем код как использованный
        code_obj.is_used = True
        code_obj.save()

        # Подтверждаем email пользователя
        user.is_verified = True
        user.save()

        # Красивое HTML-письмо для подтверждения email
        subject = "Ваш email подтверждён"
        message = format_html(
            """
            <h2>Поздравляем, {name}!</h2>
            <p>Ваш email <b>{email}</b> успешно подтверждён.</p>
            <p>Теперь вы можете войти в систему, используя свои данные для входа.</p>
            """,
            name=user.first_name or user.email,
            email=user.email
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Email подтверждён. Письмо с подтверждением отправлено.",
            "redirect": "login"
        })



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.html import format_html
from django.core.exceptions import ObjectDoesNotExist

class VerifyLoginCodeView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        # Проверка существования пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Проверка кода подтверждения
        try:
            code_obj = EmailCode.objects.get(user=user, code=code, is_used=False)
        except EmailCode.DoesNotExist:
            return Response({"error": "Неверный или уже использованный код"}, status=400)

        if not code_obj.is_valid():
            return Response({"error": "Код истёк или уже использован"}, status=400)

        # Отмечаем код как использованный
        code_obj.is_used = True
        code_obj.save()

        # Генерация токенов для входа
        refresh = RefreshToken.for_user(user)

        # Красивое HTML-письмо о успешном входе
        subject = "Вы успешно вошли в систему"
        message = format_html(
            """
            <h2>Добро пожаловать, {name}!</h2>
            <p>Вы успешно вошли в систему с email: <b>{email}</b></p>
            <p>Если это были не вы, пожалуйста, немедленно смените пароль.</p>
            """,
            name=user.first_name or user.email,
            email=user.email
        )

        send_pretty_email(email, subject, message)

        return Response({
            "message": "Вход выполнен успешно. Письмо отправлено на email.",
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })