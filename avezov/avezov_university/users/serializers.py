from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VerificationCode, UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериалайзер пользователя"""

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'is_verified']


class RegisterSerializer(serializers.Serializer):
    """Регистрация"""
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=128, min_length=6, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email уже зарегистрирован')
        return value

    def create(self, validated_data):
        # Создаем пользователя
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )

        # Создаем профиль
        UserProfile.objects.create(user=user)

        # Генерируем код
        code = VerificationCode.generate_code()
        expires_at = timezone.now() + timedelta(minutes=10)

        VerificationCode.objects.create(
            user_email=user.email,
            code=code,
            expires_at=expires_at,
            purpose='register'
        )

        return user, code


class LoginSerializer(serializers.Serializer):
    """Логин"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден')

        if not user.check_password(password):
            raise serializers.ValidationError('Неверный пароль')

        attrs['user'] = user
        return attrs


class VerifyCodeSerializer(serializers.Serializer):
    """Верификация кода"""
    code = serializers.CharField(max_length=4, min_length=4)