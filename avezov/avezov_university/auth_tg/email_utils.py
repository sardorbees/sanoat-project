from django.core.mail import send_mail
from django.conf import settings

def send_reset_code_email(email, code):
    send_mail(
        subject="Восстановление пароля",
        message=f"Ваш код для восстановления пароля: {code}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False
    )
