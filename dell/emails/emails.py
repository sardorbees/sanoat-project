from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

def send_pretty_email(to_email, subject, html_message):
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        html_message=html_message,
        fail_silently=False,
    )