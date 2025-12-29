from rest_framework import serializers
from .models import TelegramUser
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password

# -------------------
# Регистрация
# -------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = TelegramUser
        fields = ('name', 'surname', 'email', 'password', 'confirm_password')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = TelegramUser.objects.create(
            name=validated_data['name'],
            surname=validated_data['surname'],
            email=validated_data['email'],
            password=make_password(validated_data['password']),
            is_active=False
        )
        return user
# -------------------
# Вход
# -------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        try:
            user = TelegramUser.objects.get(email=email)
        except TelegramUser.DoesNotExist:
            raise serializers.ValidationError("Неверный email или пароль")

        if not user.check_old_or_current_password(password):
            raise serializers.ValidationError("Неверный email или пароль")

        data['user'] = user
        return data

# -------------------
# Проверка кода (Register/Login)
# -------------------
from rest_framework import serializers

from rest_framework import serializers


from rest_framework import serializers

class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(
        required=True,
        min_length=4,
        max_length=4,
        help_text="Одноразовый код из email"
    )

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Код должен состоять из 4 цифр")
        return value

# -------------------
# Сброс пароля: проверка кода
# -------------------
class VerifyResetCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    code = serializers.CharField(max_length=6)

# -------------------
# Сброс пароля: установка нового
# -------------------
class NewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6)

# -------------------
# Профиль пользователя
# -------------------
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = [
            "telegram_id", "name", "surname", "phone",
            "passport_id", "attestation_doc", "photo"
        ]
        read_only_fields = ["telegram_id"]

    def validate_attestation_doc(self, value):
        if value and not str(value.name).lower().endswith('.pdf'):
            raise serializers.ValidationError("Документ аттестации должен быть в формате PDF")
        return value

from rest_framework import serializers

class TelegramAuthSerializer(serializers.Serializer):
    phone = serializers.CharField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

from rest_framework import serializers
from django.contrib.auth.models import User

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username"]

from rest_framework import serializers

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email не найден")
        return value

from rest_framework import serializers

class ResendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

from rest_framework import serializers
from .models import Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'username', 'email', 'phone', 'telegram_chat_id')

from rest_framework import serializers
from .models import Users

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar', 'phone', 'birthdate', 'passport', 'jshshir']

from rest_framework import serializers

class CreateTelegramCodeSerializer(serializers.Serializer):
    phone = serializers.CharField()
    telegram_id = serializers.IntegerField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

# serializers.py
from rest_framework import serializers
from .models import TelegramAuthCode

class CreateCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramAuthCode
        fields = ["phone", "telegram_id"]

# auth_tg/serializers.py
from rest_framework import serializers
from .models import TelegramCode  # предполагается, что есть модель TelegramCode

class TelegramCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramCode
        fields = ['phone', 'telegram_id', 'first_name', 'last_name', 'code']

    def create(self, validated_data):
        import random, string
        # Генерация случайного кода
        validated_data['code'] = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        return super().create(validated_data)

# auth_tg/serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import TelegramUser, OTP


class ChangesPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def save(self, **kwargs):
        email = self.validated_data['email']
        code = self.validated_data['code']
        new_password = self.validated_data['new_password']

        user = TelegramUser.objects.get(email=email)
        otp = OTP.objects.filter(user=user, code=code, is_used=False, expires_at__gte=timezone.now()).first()
        if not otp:
            raise serializers.ValidationError("Неверный или просроченный код")

        user.set_password(new_password)
        user.save()

        otp.is_used = True
        otp.save()
        return user

class ResetsPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4)  # 4 цифры
    new_password = serializers.CharField(min_length=6)

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField(min_length=6)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PasswordResetCode

class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4)
    new_password = serializers.CharField(min_length=4)
