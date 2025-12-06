from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser
from .serializers import RegisterSerializer, UserProfileSerializer
from .models import Address
from .serializers import AddressSerializer
from rest_framework.permissions import AllowAny

class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)  # частичное обновление
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"detail": "Вы вышли"}, status=status.HTTP_200_OK)

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": f"Добро пожаловать, {request.user.first_name}!"})

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(old_password):
            return Response({"error": "Неверный текущий пароль"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Пароль успешно изменён ✅"})

from .utils import send_sms_eskiz


class ChangePasswordAPIView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Avval login qiling"}, status=401)

        new_password = request.data.get("new_password")

        if not new_password or len(new_password) < 6:
            return Response({"error": "Parol kamida 6 belgidan iborat bo'lishi kerak"}, status=400)

        request.user.set_password(new_password)
        request.user.must_change_password = False
        request.user.save()

        return Response({"message": "Parol muvaffaqiyatli o'zgartirildi"})


import requests

def send_sms_to_user(phone, message):
    try:
        token_response = requests.post('https://notify.eskiz.uz/api/auth/login', data={
            'email': 'ваш_email',
            'password': 'ваш_пароль',
        })
        token = token_response.json()['data']['token']

        requests.post('https://notify.eskiz.uz/api/message/sms/send', data={
            'mobile_phone': phone,
            'message': message,
            'from': '4546',  # или ваше значение
            'callback_url': 'http://yourdomain.uz/callback/',
        }, headers={'Authorization': f'Bearer {token}'})
    except Exception as e:
        print('Ошибка при отправке SMS:', e)

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Address
from .serializers import AddressSerializer

class AddressListCreateView(ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только адреса текущего пользователя
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # При создании автоматически привязываем адрес к текущему пользователю
        serializer.save(user=self.request.user)

class AddressDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'address_id'

    def get_queryset(self):
        # Доступ только к своим адресам
        return Address.objects.filter(user=self.request.user)


import random
import string
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response

User = get_user_model()

class ResetPasswordAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Email topilmadi"}, status=404)

        # Random yangi parol generatsiya qilish
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # Parolni yangilash
        user.set_password(new_password)
        user.save()

        # Gmail orqali yuborish
        send_mail(
            subject="Parolingiz qayta tiklandi",
            message=f"Assalomu alaykum!\n\nSizning yangi parolingiz:\n{new_password}\n\nIltimos parolni kirgandan keyin o‘zgartiring!",
            from_email="youremail@gmail.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"message": "Yangi parol emailga yuborildi"})

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from .models import CustomUser


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User created. Verification code sent to email."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response({"error": "Email and code required"}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if str(user.verification_code) == str(code):
            user.is_verified = True
            user.verification_code = ""
            user.save()
            return Response({"message": "Code verified successfully"})

        return Response({"error": "Invalid code"}, status=400)

