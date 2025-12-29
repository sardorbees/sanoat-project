from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.hashers import make_password
from datetime import timedelta
from django.utils import timezone
import random
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.hashers import check_password

class UserManager(BaseUserManager):
    def create_user(self, email, name, surname, phone, password=None):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, surname=surname, phone=phone)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, surname, phone, password):
        user = self.create_user(email, name, surname, phone, password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class TelegramUser(models.Model):
    telegram_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    password = models.CharField(max_length=128, blank=True, null=True)
    previous_password = models.CharField(max_length=128, blank=True, null=True)
    verification_code = models.CharField(
        max_length=4,
        unique=True,
        null=True,
        blank=True
    )
    verification_code_created_at = models.DateTimeField(blank=True, null=True)
    reset_code = models.CharField(max_length=6, blank=True, null=True)
    reset_code_created_at = models.DateTimeField(blank=True, null=True)

    photo = models.ImageField(upload_to="photos/", blank=True, null=True)
    passport_id = models.CharField(max_length=50, blank=True, null=True)
    profile_photopassport_id = models.FileField(upload_to="attestations/", blank=True, null=True)
    attestation_doc = models.FileField(upload_to="attestations/", blank=True, null=True)
    profile_photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    code_created_at = models.DateTimeField(null=True, blank=True)
    code_expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def check_old_or_current_password(self, raw_password):
        # проверка текущего пароля
        if self.password and check_password(raw_password, self.password):
            return True
        # проверка предыдущего пароля
        if self.previous_password and check_password(raw_password, self.previous_password):
            return True
        return False

    reset_attempts = models.PositiveIntegerField(default=0)
    reset_blocked_until = models.DateTimeField(null=True, blank=True)

    failed_attempts = models.IntegerField(default=0)
    is_blocked = models.BooleanField(default=False)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def generate_code(self):
        import random
        from django.utils import timezone
        code = str(random.randint(1000, 9999))
        self.verification_code = code
        self.verification_code_created_at = timezone.now()
        self.save()
        return code

    def generate_verification_code(self):
        self.verification_code = f"{random.randint(1000, 9999)}"  # 4 цифры
        self.code_created_at = timezone.now()
        self.code_expires_at = timezone.now() + timedelta(minutes=5)  # срок 5 минут
        self.save(update_fields=['verification_code', 'code_created_at', 'code_expires_at'])
        return self.verification_code

    def code_is_valid(self, code):
        return (
            self.verification_code == code and
            self.code_expires_at and
            timezone.now() < self.code_expires_at
        )

    def is_reset_code_valid(self):
        if self.reset_code_created_at and timezone.now() - self.reset_code_created_at < timedelta(minutes=40):
            return True
        return False

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
import string

class TelegramAuthCode(models.Model):
    phone = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100, blank=True)
    telegram_id = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    auth_code = models.CharField(max_length=32, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=255, unique=True, blank=True, null=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.auth_code:
            self.auth_code = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.phone} - {self.code}"


from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class VerificationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.code}"


from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.URLField(blank=True, null=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    fish = models.CharField(
        max_length=255,
        verbose_name="FISH",
        blank=True
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Telefon",
        blank=True
    )
    birthdate = models.DateField(
        null=True,
        blank=True,
        verbose_name="Tug'ilgan sana"
    )
    passport = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Passport"
    )
    jshshir = models.CharField(
        max_length=14,
        blank=True,
        verbose_name="JSHSHIR"
    )

    def __str__(self):
        return self.fish or self.user.username

from django.contrib.auth.models import AbstractUser
from django.db import models

class Users(AbstractUser):
    avatar = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    birthdate = models.DateField(blank=True, null=True)
    passport = models.CharField(max_length=50, blank=True)
    jshshir = models.CharField(max_length=50, blank=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # изменили related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # изменили related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return self.username

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid

class TelegramLoginCode(models.Model):
    telegram_id = models.BigIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    code = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.phone} | {self.code}"

from django.db import models

class TelegramCode(models.Model):
    phone = models.CharField(max_length=20)
    telegram_id = models.BigIntegerField(null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.phone} - {self.code}"

# auth_tg/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.username} - {self.code}"

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        # Токен действителен 1 час
        return timezone.now() > self.created_at + timezone.timedelta(hours=1)


from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PasswordAttempt(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    attempts = models.PositiveIntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)


import random
import string
from datetime import timedelta
from django.db import models
from django.utils import timezone

class OTP(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, null=True, blank=True)
    code = models.CharField(max_length=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(random.randint(1000, 9999))  # генерируем 6-значный код
        super().save(*args, **kwargs)

    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 300


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PendingPassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pending_password')
    new_password = models.CharField(max_length=128)  # хранить хэш
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

