from django.core.mail import send_mail
from django.conf import settings

def send_pretty_email(email, subject, message):
    html_message = f"""
    <div style='background:#f5f5f5;padding:20px;font-family:Arial;border-radius:10px;'>
        <div style='max-width:500px;margin:auto;background:white;padding:20px;border-radius:10px;'>
            <h2 style='color:#333;text-align:center;'>{subject}</h2>
            <p style='font-size:16px;color:#555;'>{message}</p>
        </div>
    </div>
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
        html_message=html_message,
    )

import random

def generate_code():
    return str(random.randint(100000, 999999))


from django.core.mail import EmailMultiAlternatives

def send_password_verify_code(email, code):
    subject = "Подтверждение смены пароля"
    from_email = "no-reply@example.com"

    text_content = f"Ваш код подтверждения: {code}"

    html_content = f"""
    <html>
    <body style="font-family: Arial; background:#f2f2f2; padding:20px;">
      <div style="max-width:600px;margin:auto;background:white;padding:25px;border-radius:10px;">
        <h2 style="color:#333;">Подтверждение смены пароля</h2>
        <p>Введите этот код, чтобы завершить изменение пароля:</p>
        <p style="font-size:32px;font-weight:bold;color:#1a73e8;text-align:center;">{code}</p>
        <p>Код действует 10 минут.</p>
        <hr>
        <p style="font-size:12px;color:#888;">Если это были не вы — срочно смените пароль.</p>
      </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


from django.core.mail import EmailMultiAlternatives

def send_pretty_email(to_email, subject, html_content):
    msg = EmailMultiAlternatives(subject, "", None, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


import string
import random

def generate_new_password(length: int = 10) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))
