from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserICafeMapping

# Настройка кастомного UserAdmin
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("nickname", "phone", "full_name", "xp_points", "level", "created_at", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "level")
    search_fields = ("phone", "nickname", "full_name")
    ordering = ("created_at",)
    readonly_fields = ("level", "xp_points", "created_at")

    fieldsets = (
        (None, {"fields": ("phone", "nickname", "password")}),
        ("Personal Info", {"fields": ("full_name", "avatar_url", "xp_points", "level")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "nickname", "password1", "password2", "is_staff", "is_active")
        }),
    )


# Админ для iCafe Mapping
class UserICafeMappingAdmin(admin.ModelAdmin):
    list_display = ("user", "branch_id", "icafe_member_id", "icafe_member_group_id")
    search_fields = ("user__nickname", "icafe_member_id")
    list_filter = ("icafe_member_group_id",)

# Регистрация моделей
admin.site.register(User, UserAdmin)
admin.site.register(UserICafeMapping, UserICafeMappingAdmin)
