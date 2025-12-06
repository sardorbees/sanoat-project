import requests

ESKIZ_API_TOKEN = "tvF4OWO2dXEu7ejGc7WGIjkmNA2prIQOXbzIR7q6"  # Вставь свой боевой токен
ESKIZ_BASE_URL = "https://notify.eskiz.uz/api"

def send_sms(phone, message):
    """
    Отправка реального SMS через Eskiz
    Работает только с боевым токеном и положительным балансом
    """
    url = f"{ESKIZ_BASE_URL}/message/sms/send"
    headers = {
        "Authorization": f"Bearer {ESKIZ_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "mobile_phone": phone,
        "message": message,
        "from": "4546"  # стандартный Eskiz отправитель
    }
    response = requests.post(url, json=data, headers=headers)
    try:
        return response.json()
    except:
        return {"status": "error", "raw_text": response.text}
