# emails/fields.py
from django.db import models
from django.utils.encoding import force_str
from .crypto import encrypt_text, decrypt_text

class EncryptedTextField(models.TextField):
    """
    Stores encrypted base64 string in DB. Python value is plain string.
    """
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return decrypt_text(value)
        except Exception:
            # если неудача — вернуть raw значение, чтобы не ломать чтение
            return value

    def get_prep_value(self, value):
        if value is None:
            return value
        # ensure string
        return encrypt_text(force_str(value))

class EncryptedCharField(models.CharField):
    """
    For short strings (emails, phone) — stores encrypted base64 in db (so length must be enough).
    NOTE: Encrypted output length is larger than input; so set max_length generously or use TextField.
    """
    description = "Encrypted CharField (stores base64 of AES-GCM blob)"

    def __init__(self, *args, **kwargs):
        # We store base64 blob, which can be longer. If user didn't set max_length, set a default.
        if "max_length" not in kwargs:
            kwargs["max_length"] = 512
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return decrypt_text(value)
        except Exception:
            return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return encrypt_text(str(value))
