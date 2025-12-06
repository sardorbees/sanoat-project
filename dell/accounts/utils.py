import requests

def send_sms_eskiz(phone_number, message):
    token = "ВАШ_EKIZ_TOKEN"
    url = "https://notify.eskiz.uz/api/message/sms/send"

    headers = {
        "Authorization": f"Bearer {token}",
    }

    data = {
        "mobile_phone": phone_number,
        "message": message,
        "from": "4546",  # это код отправителя (можно оставить как есть)
        "callback_url": ""
    }

    response = requests.post(url, headers=headers, data=data)
    return response.json()

from django.core.mail import send_mail

def send_reset_password_email(email, code):
    subject = "Parolni tiklash kodi"
    message = f"Sizning tasdiqlash kodingiz: {code}"
    send_mail(subject, message, None, [email])

