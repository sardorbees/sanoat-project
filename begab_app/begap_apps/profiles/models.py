import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# Менеджер пользователя
class UserManager(BaseUserManager):
    def create_user(self, phone, nickname, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone must be set")
        if not nickname:
            raise ValueError("Nickname must be set")
        user = self.model(phone=phone, nickname=nickname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, nickname, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone, nickname, password, **extra_fields)

# Модель пользователя
class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, unique=True, db_index=True)
    nickname = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    xp_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # ВАЖНО: уникальные related_name для групп и разрешений
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["nickname"]

    def __str__(self):
        return self.nickname

    def save(self, *args, **kwargs):
        self.level = self.xp_points // 100  # вычисляем уровень автоматически
        super().save(*args, **kwargs)


# Связка с iCafe
class UserICafeMapping(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="icafe_mappings")
    branch_id = models.UUIDField()
    icafe_member_id = models.CharField(max_length=50)
    icafe_member_group_id = models.IntegerField()

    def __str__(self):
        return f"{self.user.nickname} - {self.icafe_member_id}"
