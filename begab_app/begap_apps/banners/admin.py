from django.contrib import admin
from .models import Banner, Club

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("id", "action_link", "priority", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("action_link",)
    ordering = ("-priority", "-created_at")


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "rating")
    search_fields = ("name",)
    ordering = ("-rating",)
