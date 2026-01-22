from django.contrib import admin
from .models import PaymentMethod

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'is_default', 'created_at')
    list_filter = ('type', 'is_default')
    search_fields = ('title', 'masked_number')
