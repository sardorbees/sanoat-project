from celery import shared_task
import time

@shared_task
def send_test_email(email):
    # Тут может быть реальный код отправки email
    print(f"Отправка тестового email на {email}")
    time.sleep(5)
    return f"Email успешно отправлен на {email}"
