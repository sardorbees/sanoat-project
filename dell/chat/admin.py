from django.contrib import admin
from .models import ChatMessage, EmailLog, OnlineStatus
from django.contrib import admin
from .models import ChatMessage, BlockedUser
from django.utils.html import format_html

from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import OnlineStatus


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "user_display", "is_admin", "is_read", "created_at", 'voice')
    list_filter = ("is_admin", "is_read", "created_at")
    search_fields = ("user__username", "content")
    ordering = ("-created_at",)

    @admin.display(description="Пользователь")
    def user_display(self, obj):
        status = getattr(obj.user, "online_status", None)

        if status and status.is_online:
            return format_html(
                '<span>🟢 <b>{}</b></span>',
                obj.user.username
            )
        return format_html(
            '<span>⚫ {}</span>',
            obj.user.username
        )

    @admin.display(description="Сообщение")
    def short_content(self, obj):
        return obj.content[:30] + ("..." if len(obj.content) > 30 else "")

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient','subject','status','created_at')
    readonly_fields = ('recipient','subject','body','status','error','created_at')
    list_filter = ('status','created_at')

class OnlineFilter(admin.SimpleListFilter):
    title = "Online"
    parameter_name = "online"

    def lookups(self, request, model_admin):
        return [('yes', 'Online'), ('no', 'Offline')]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'yes':
            return queryset.filter(last_seen__gte=now - timedelta(seconds=15))
        if self.value() == 'no':
            return queryset.filter(last_seen__lt=now - timedelta(seconds=15))
        return queryset


@admin.register(OnlineStatus)
class OnlineStatusAdmin(admin.ModelAdmin):
    list_display = ("user", "online_display", "is_online", "is_typing", "last_seen", 'is_online_status')
    list_filter = ("is_typing", OnlineFilter)
    search_fields = ("user__username", "user__email")

    @admin.display(description="Статус")
    def online_display(self, obj):
        if obj.is_online:
            return format_html('<span style="color: green; font-weight:bold;">🟢 Online</span>')
        return format_html('<span style="color: red; font-weight:bold;">🔴 Offline</span>')

    def is_online_status(self, obj):
        return obj.is_online
    is_online_status.boolean = True
    is_online_status.short_description = "Online"

@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address")
    search_fields = ("user__username", "ip_address")