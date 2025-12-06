from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from cryptography.fernet import Fernet
import random

fernet = Fernet(settings.FERNET_KEY)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_encrypted = models.BinaryField(default=b"")
    image = models.URLField(blank=True, null=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_created_at = models.DateTimeField(blank=True, null=True)
    must_change_password = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name='accounts_customuser_set',  # <-- o'zgartirdik
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='accounts_customuser_permissions_set',  # <-- o'zgartirdik
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def generate_code(self):
        import random
        self.email_verification_code = str(random.randint(100000, 999999))
        self.save()
        return self.email_verification_code

    @property
    def phone_number(self):
        if self.phone_encrypted:
            return fernet.decrypt(self.phone_encrypted).decode()
        return ""

    @phone_number.setter
    def phone_number(self, value):
        self.phone_encrypted = fernet.encrypt(value.encode())

class UserManager(BaseUserManager):
    def create_user(self, phone, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")
        user = self.model(**extra_fields)
        user.phone_number = phone  # автоматически шифруем
        user.set_unusable_password()
        user.save()
        return user

class User(AbstractBaseUser):
    phone_encrypted = models.BinaryField(default=b"")
    is_active = models.BooleanField(default=True)

    @property
    def phone(self):
        if self.phone_encrypted:
            return fernet.decrypt(self.phone_encrypted).decode()
        return ""

    @phone.setter
    def phone(self, value):
        self.phone_encrypted = fernet.encrypt(value.encode())

    USERNAME_FIELD = 'phone_encrypted'
    objects = UserManager()

    def __str__(self):
        return self.phone

class OTP(models.Model):
    phone_encrypted = models.BinaryField(default=b"")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def phone(self):
        if self.phone_encrypted:
            return fernet.decrypt(self.phone_encrypted).decode()
        return ""


    @phone.setter
    def phone(self, value):
        self.phone_encrypted = fernet.encrypt(value.encode())

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='addresses', on_delete=models.CASCADE)
    street_encrypted = models.BinaryField(default=b"")
    city_encrypted = models.BinaryField(default=b"")
    country_encrypted = models.BinaryField(default=b"")

    @property
    def street(self):
        return fernet.decrypt(self.street_encrypted).decode()

    @street.setter
    def street(self, value):
        self.street_encrypted = fernet.encrypt(value.encode())

    @property
    def city(self):
        return fernet.decrypt(self.city_encrypted).decode()

    @city.setter
    def city(self, value):
        self.city_encrypted = fernet.encrypt(value.encode())

    @property
    def country(self):
        return fernet.decrypt(self.country_encrypted).decode()

    @country.setter
    def country(self, value):
        self.country_encrypted = fernet.encrypt(value.encode())

    def __str__(self):
        return f"{self.street}, {self.city}, {self.country}"

from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'phone_number']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.phone_number = validated_data['phone_number']
        user.set_password(validated_data['password'])
        user.save()
        return user
