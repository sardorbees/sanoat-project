from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, LoginSerializer, VerifyCodeSerializer,
    UserSerializer
)
from .models import VerificationCode, CustomUser, UserProfile
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class RegisterView(APIView):
    """
    POST /api/auth_tg/register/
    {
        "first_name": "Sardor",
        "last_name": "Rizayev",
        "email": "user@example.com",
        "password": "password123"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Проверьте данные',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user, code = serializer.save()

            return Response({
                'success': True,
                'message': 'Код отправлен',
                'code': code,
                'email': user.email,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RegisterVerifyCodeView(APIView):
    """
    POST /api/auth_tg/register-verify-code/
    {
        "code": "1234"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Код не указан'
            }, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']

        try:
            verification = VerificationCode.objects.get(
                code=code,
                purpose='register',
                is_used=False
            )
        except VerificationCode.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Неверный код'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not verification.is_valid():
            return Response({
                'success': False,
                'error': 'Код истек'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Помечаем как использованный
        verification.is_used = True
        verification.save()

        try:
            user = User.objects.get(email=verification.user_email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Пользователь не найден'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Активируем пользователя
        user.is_verified = True
        user.save()

        # Генерируем токены
        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'Успешная регистрация!',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    POST /api/auth_tg/login/
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']

        # Удаляем старые коды
        VerificationCode.objects.filter(
            user_email=user.email,
            purpose='login',
            is_used=False
        ).delete()

        # Генерируем новый код
        code = VerificationCode.generate_code()
        expires_at = timezone.now() + timedelta(minutes=10)

        VerificationCode.objects.create(
            user_email=user.email,
            code=code,
            expires_at=expires_at,
            purpose='login'
        )

        return Response({
            'success': True,
            'message': 'Код отправлен',
            'code': code,
            'email': user.email
        }, status=status.HTTP_200_OK)


class LoginVerifyCodeView(APIView):
    """
    POST /api/auth_tg/login-verify-code/
    {
        "code": "5678"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Код не указан'
            }, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']

        try:
            verification = VerificationCode.objects.get(
                code=code,
                purpose='login',
                is_used=False
            )
        except VerificationCode.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Неверный код'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not verification.is_valid():
            return Response({
                'success': False,
                'error': 'Код истек'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Помечаем как использованный
        verification.is_used = True
        verification.save()

        try:
            user = User.objects.get(email=verification.user_email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Пользователь не найден'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Генерируем токены
        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'Успешный вход!',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class ProfileView(APIView):
    """
    GET /api/auth_tg/profile/
    Headers: Authorization: Bearer {token}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            profile = UserProfile.objects.get(user=user)

            return Response({
                'success': True,
                'message': 'Профиль загружен',
                'user': UserSerializer(user).data,
                'profile': {
                    'avatar': profile.avatar.url if profile.avatar else None,
                    'bio': profile.bio,
                    'personal_info': profile.personal_info
                }
            }, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Профиль не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)