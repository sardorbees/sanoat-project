import re
from django.core.exceptions import ValidationError

def validate_password_strength(password):
    if len(password) < 8:
        raise ValidationError("Пароль должен быть минимум 8 символов")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Добавьте заглавную букву")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Добавьте строчную букву")

    if not re.search(r"\d", password):
        raise ValidationError("Добавьте цифру")

    if not re.search(r"[!@#$%^&*()_+=\-{}[\]:;\"'<>,.?/]", password):
        raise ValidationError("Добавьте спецсимвол")
