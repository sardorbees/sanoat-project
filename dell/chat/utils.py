from django.core.mail import send_mail
from django.conf import settings

def send_email_async(to_email, subject, message):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=False
    )

from django.core.mail import send_mail
from django.conf import settings

BAD_WORDS = ["плохое_слово1", "плохое_слово2", "мат", "ругательство"]

def contains_bad_words(text):
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            return True
    return False


from channels.db import database_sync_to_async
from rest_framework_simplejwt.authentication import JWTAuthentication

jwt_auth = JWTAuthentication()

@database_sync_to_async
def get_user_from_token(token):
    # token: raw access token string
    validated = jwt_auth.get_validated_token(token)
    return jwt_auth.get_user(validated)

from .models import ChatMessage
from django.utils import timezone

@database_sync_to_async
def create_message(user_obj, sender_is_admin, content=None, attachment=None):
    msg = ChatMessage.objects.create(
        user=user_obj,
        sender_is_admin=sender_is_admin,
        content=content,
        attachment=attachment,
        status=ChatMessage.STATUS_SENT,
    )
    return msg

@database_sync_to_async
def mark_message_delivered(msg_id):
    try:
        msg = ChatMessage.objects.get(pk=msg_id)
    except ChatMessage.DoesNotExist:
        return None
    msg.status = ChatMessage.STATUS_DELIVERED
    msg.delivered_at = timezone.now()
    msg.save(update_fields=["status", "delivered_at"])
    return msg

@database_sync_to_async
def mark_message_read(msg_id):
    try:
        msg = ChatMessage.objects.get(pk=msg_id)
    except ChatMessage.DoesNotExist:
        return None
    msg.status = ChatMessage.STATUS_READ
    msg.read_at = timezone.now()
    msg.save(update_fields=["status", "read_at"])
    return msg