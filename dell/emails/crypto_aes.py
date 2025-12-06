import base64
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from django.conf import settings


def encrypt_aes(data: str) -> str:
    if data is None:
        return None

    key = bytes.fromhex(settings.AES_PRIMARY_KEY)
    cipher = AES.new(key, AES.MODE_GCM)

    ciphertext, tag = cipher.encrypt_and_digest(data.encode())

    result = cipher.nonce + tag + ciphertext
    return base64.b64encode(result).decode()


def decrypt_aes(token: str) -> str:
    if token is None:
        return None

    raw = base64.b64decode(token)

    nonce = raw[:16]
    tag = raw[16:32]
    ciphertext = raw[32:]

    # Перебор всех ключей (ротация)
    for hex_key in settings.AES_KEYS:
        key = bytes.fromhex(hex_key)

        try:
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            data = cipher.decrypt_and_verify(ciphertext, tag)
            return data.decode()
        except Exception:
            continue

    raise ValueError("Invalid AES token")
