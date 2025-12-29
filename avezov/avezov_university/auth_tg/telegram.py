import requests
from django.conf import settings

def send_code(code, action, telegram_id):
    """
    Отправка кода или уведомления через Telegram Bot.
    action: 'register', 'login', 'login_success' и т.д.
    """
    if not telegram_id:
        return False

    text = f"[{action.upper()}] Ваш код: {code}" if action in ["register", "login"] else code

    # Пример через Bot API
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text
    }
    try:
        response = requests.post(url, data=payload)
        return response.status_code == 200
    except Exception as e:
        print("Telegram send error:", e)
        return False