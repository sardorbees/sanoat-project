from django.db.models import CharField, TextField
from .crypto_aes import encrypt_aes, decrypt_aes


class AESCharField(CharField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_aes(value)

    def get_prep_value(self, value):
        if value is None:
            return None
        return encrypt_aes(value)


class AESTextField(TextField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_aes(value)

    def get_prep_value(self, value):
        if value is None:
            return None
        return encrypt_aes(value)
