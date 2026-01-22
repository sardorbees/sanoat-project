from django.contrib import admin
from .models import Branch, Seat, Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "seat_id",
        "status",
        "start_time",
        "end_time",
        "total_amount",
        "penalty_amount",
        'service_name',
        'visit_datetime',
    )

    list_filter = (
        "status",
        "start_time",
        "end_time",
    )

    search_fields = (
        "user__username",
        "user__phone",
        "seat_id",
        "icafe_session_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    readonly_fields = ("id", "user", "start_time", "end_time", "status")
    can_delete = False

# --- Админ для Branch ---
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

# --- Админ для Seat ---
@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("number", "branch", "status")
    list_filter = ("branch", "status")
    search_fields = ("number", "branch__name")
    inlines = [BookingInline]