from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet

fernet = Fernet(settings.FERNET_KEY)

class EncryptedCharField(models.Field):
    description = "CharField с автоматическим шифрованием"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 255)
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'BinaryField'

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return fernet.decrypt(value).decode()

    def to_python(self, value):
        if value is None or isinstance(value, str):
            return value
        return fernet.decrypt(value).decode()

    def get_prep_value(self, value):
        if value is None:
            return value
        return fernet.encrypt(value.encode())


class EncryptedTextField(models.Field):
    description = "TextField с автоматическим шифрованием"

    def get_internal_type(self):
        return 'BinaryField'

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return fernet.decrypt(value).decode()

    def to_python(self, value):
        if value is None or isinstance(value, str):
            return value
        return fernet.decrypt(value).decode()

    def get_prep_value(self, value):
        if value is None:
            return value
        return fernet.encrypt(value.encode())
