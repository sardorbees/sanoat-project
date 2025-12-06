from django.contrib import admin

from myblogyourapp.models import *


@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    list_display_links = ("title",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at", "is_published")
    list_display_links = ("title",)
    list_editable = ("is_published",)
