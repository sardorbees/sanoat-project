from django.contrib import admin
from .models import TelegramUser, TelegramAuthCode


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_id", "email", "name", "surname", "phone", "photo", "attestation_doc", "profile_photo"
        "passport_id", "verification_code", "reset_code", "reset_code_created_at", "phone", "photo"
    )
    search_fields = ("telegram_id", "email", "name", "surname", "phone")
    readonly_fields = ("verification_code", "reset_code", "reset_code_created_at")

    fieldsets = (
        ("Основная информация", {
            "fields": ("telegram_id", "email", "name", "surname", "phone")
        }),
        ("Паспорт", {
            "fields": ("passport_id",)
        }),
        ("Коды подтверждения", {
            "fields": ("verification_code", "reset_code", "reset_code_created_at")
        }),
    )

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Users

@admin.register(Users)
class UserAdmin(BaseUserAdmin):
    model = Users
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'avatar', 'google_id')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'google_id')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'avatar', 'google_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

from django.contrib import admin
from .models import TelegramLoginCode

@admin.register(TelegramLoginCode)
class TelegramLoginCodeAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "telegram_id",
        "code",
        "is_used",
        "created_at",
        "expires_at",
    )
    readonly_fields = ("code", "created_at", "expires_at")

# users/admin.py
from django.contrib import admin
from .models import PasswordResetCode

@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "is_used")
    list_filter = ("is_used", "created_at")
    search_fields = ("user__username", "user__email", "code")

