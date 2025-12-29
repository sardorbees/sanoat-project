from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'question', 'created_at')
    search_fields = ('full_name', 'phone_number', 'question')
    list_filter = ('created_at',)
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Контактная информация", {
            "fields": ("full_name", "phone_number", "email")
        }),
        ("Вопрос", {
            "fields": ("question",)
        }),
        ("Дополнительно", {
            "fields": ("created_at",)
        }),
    )
