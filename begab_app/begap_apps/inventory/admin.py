from django.contrib import admin
from .models import Branch, Zone, Seat

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "club_id")
    search_fields = ("name", "address", "club_id")

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "branch", "type", "price_per_hour")
    list_filter = ("type",)
    search_fields = ("name", "branch__name")

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("number", "zone", "icafe_pc_name", "is_active")
    list_filter = ("is_active", "zone__type")
    search_fields = ("number", "icafe_pc_name")
