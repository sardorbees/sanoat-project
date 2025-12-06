from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address
import random

class AddressInline(admin.TabularInline):
    model = Address
    extra = 1
    fields = ('street', 'city', 'country')

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from .models import CustomUser
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_staff', 'phone_number']
    readonly_fields = ['phone_number']  # так как это property

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'image')}),
    )

    def send_verification_code(self, request, queryset):
        for user in queryset:
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            user.verification_code = code
            user.save()

            send_mail(
                "Your Verification Code",
                f"Hello {user.username}, your code is: {code}",
                "from@example.com",
                [user.email],
                fail_silently=False,
            )
        self.message_user(request, "Verification code(s) sent successfully!")

    send_verification_code.short_description = "Send verification code to selected users"
    def save_model(self, request, obj, form, change):
        raw_password = form.cleaned_data.get("password1") or form.cleaned_data.get("password")
        super().save_model(request, obj, form, change)
        if not change:
            if raw_password:
                send_mail(
                    subject="Sizning login ma'lumotlaringiz",
                    message=f"Assalomu alaykum!\n\nSizning login ma'lumotlaringiz:\n\n"
                            f"Login: {obj.email or obj.username}\n"
                            f"Parol: {raw_password}\n\n"
                            f"Iltimos parolni kirgandan so‘ng o‘zgartiring!",
                    from_email="youremail@gmail.com",
                    recipient_list=[obj.email],
                    fail_silently=False,
                )
