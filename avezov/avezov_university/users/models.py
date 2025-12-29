from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import random
import string
from datetime import timedelta
from django.utils import timezone


class CustomUser(AbstractUser):
    """Кастомный пользователь"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(
        Group,
        related_name='custom_users',  # <-- изменено
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_users',  # <-- изменено
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    class Meta:
        db_table = 'custom_user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class VerificationCode(models.Model):
    """Коды верификации"""
    user_email = models.EmailField(db_index=True)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    purpose = models.CharField(
        max_length=20,
        choices=[('register', 'Регистрация'), ('login', 'Логин')],
        default='register'
    )

    class Meta:
        db_table = 'verification_code'
        verbose_name = 'Код верификации'
        verbose_name_plural = 'Коды верификации'

    def __str__(self):
        return f"{self.user_email} - {self.code}"

    def is_valid(self):
        """Проверяет валидность"""
        return not self.is_used and timezone.now() < self.expires_at

    @staticmethod
    def generate_code():
        """Генерирует 4-значный код"""
        return ''.join(random.choices(string.digits, k=4))


class UserProfile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    personal_info = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f"Profile - {self.user.email}"