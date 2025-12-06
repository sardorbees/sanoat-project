from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
import random
from .fields import EncryptedTextField, EncryptedCharField
from emails.encrypted_fields_aes import AESCharField, AESTextField

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .crypto import encrypt_text, decrypt_text

from django.contrib.auth.models import AbstractUser
from django.db import models
from emails.fields import EncryptedCharField
from emails.crypto import hmac_sha256_hex
import random
import string

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Email обязателен")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(email, username, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def set_email(self, email: str):
        self.email_encrypted = encrypt_email(email)
        self.email_hmac = hmac_sha256_hex(email)
        self.save(update_fields=['email_encrypted', 'email_hmac'])

    def get_email(self) -> str:
        if self.email_encrypted:
            return decrypt_email(self.email_encrypted)
        return None

    def set_random_password(self):
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        self.set_password(password)
        self.save(update_fields=['password'])
        return password

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, blank=True)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def generate_code(self):
        self.code = str(random.randint(100000, 999999))
        self.save()
        return self.code


class ResetPasswordCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    @property
    def code(self):
        return decrypt_text(self.code_encrypted)

    @code.setter
    def code(self, value):
        self.code_encrypted = encrypt_text(value)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=4)

class EmailCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def generate_code(self, length=6):
        import random
        code = ''.join(random.choices("0123456789", k=length))
        from django.conf import settings
        from cryptography.fernet import Fernet
        fernet = Fernet(settings.FERNET_KEY)
        self.code = fernet.encrypt(code.encode()).decode()  # шифруем
        self.save()
        return code

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.created_at + timedelta(seconds=30)

