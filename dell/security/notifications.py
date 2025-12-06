# security/notifications.py
import requests
from django.conf import settings

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram send error:", e)

def send_sms(phone, message):
    # пример Eskiz API
    url = f"{settings.SMS_API_URL}/api/message/sms/send"
    data = {
        "mobile_phone": phone,
        "message": message,
        "from": settings.SMS_SENDER
    }
    headers = {"Authorization": f"Bearer {settings.SMS_API_KEY}"}
    try:
        requests.post(url, json=data, headers=headers)
    except Exception as e:
        print("SMS send error:", e)
