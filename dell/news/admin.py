from django.contrib import admin
from .models import IndustryArticle

@admin.register(IndustryArticle)
class IndustryArticleAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "year", "statistic", "image_tag", "created_at")
    list_display_links = ("id", "title")
    search_fields = ("title", "subtitle", "content", "statistic")
    list_filter = ("year",)
    readonly_fields = ("image_tag", "created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("title", "subtitle", "content", "image")
        }),
        ("Дополнительно", {
            "fields": ("year", "statistic", "image_tag", "created_at", "updated_at"),
        }),
    )
