from django.contrib import admin
from .models import IconTitle

@admin.register(IconTitle)
class IconTitleAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "number")
