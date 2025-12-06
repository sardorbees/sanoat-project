from django.contrib import admin
from .models import Info

@admin.register(Info)
class InfoAdmin(admin.ModelAdmin):
    list_display = ("id", "base_title", "title", "number")
    readonly_fields = ("title",)
