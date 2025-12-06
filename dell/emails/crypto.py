from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

# Загружаем все ключи из settings
FERNET_KEYS = settings.FERNET_KEYS

# Подготавливаем объекты Fernet
FERNETS = [
    Fernet(key.encode() if isinstance(key, str) else key)
    for key in FERNET_KEYS
]


def encrypt_text(text: str) -> str:
    """
    Шифрует строку.
    """
    if text is None:
        return None
    return FERNETS[0].encrypt(text.encode()).decode()


def decrypt_text(token: str) -> str:
    """
    Расшифровывает строку.
    Проверяет все ключи (поддержка ротации).
    """
    if token is None:
        return None

    for f in FERNETS:
        try:
            return f.decrypt(token.encode()).decode()
        except InvalidToken:
            continue

    raise InvalidToken("Invalid encryption token")


import base64
import os
import hmac
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from django.conf import settings


# ----------------------------
#   AES-256-GCM ENCRYPTION
# ----------------------------

AES_KEY = settings.AES_KEY  # 32 bytes hex


def encrypt_text(text: str) -> str:
    if text is None:
        return None

    key = bytes.fromhex(AES_KEY)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(text.encode())

    result = cipher.nonce + tag + ciphertext
    return base64.b64encode(result).decode()


def decrypt_text(token: str) -> str:
    if token is None:
        return None

    raw = base64.b64decode(token)

    nonce = raw[:16]
    tag = raw[16:32]
    ciphertext = raw[32:]

    key = bytes.fromhex(AES_KEY)

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    data = cipher.decrypt_and_verify(ciphertext, tag)
    return data.decode()

def hmac_sha256_hex(value: str) -> str:
    secret = settings.HMAC_SECRET_KEY.encode()
    return hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()


# emails/crypto.py
import os
import base64
import hashlib
from decouple import config
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from typing import Tuple

# Настройки для PBKDF2 (при выводе ключа из SECRET_KEY)
PBKDF2_ITERATIONS = 100_000
PBKDF2_SALT = b"my_cleaning_static_salt_v1"  # можно сменить на env-var, но не теряй соль при шифровании данных

def _derive_key_from_secret(secret: str, length: int = 32) -> bytes:
    """Derive a fixed-length key from SECRET_KEY using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        PBKDF2_SALT,
        PBKDF2_ITERATIONS,
        dklen=length,
    )

def get_encryption_key() -> bytes:
    """
    Returns a 32-byte key for AES-256.
    Priority:
     1) ENCRYPTION_KEY env (base64)
     2) derive from DJANGO SECRET_KEY (less ideal but works)
    """
    env_key = config("ENCRYPTION_KEY", default=None)
    if env_key:
        # Support raw base64 or hex or plain text (try base64 first)
        try:
            return base64.b64decode(env_key)
        except Exception:
            # fallback: if user provided hex
            try:
                return bytes.fromhex(env_key)
            except Exception:
                # fallback: raw bytes from string (not recommended)
                return env_key.encode("utf-8")[:32].ljust(32, b"\0")
    # fallback: derive from SECRET_KEY
    secret = config("SECRET_KEY")
    return _derive_key_from_secret(secret, 32)

def encrypt_text(plaintext: str) -> str:
    """
    Encrypt plaintext (utf-8 string) and return base64 of: nonce || tag || ciphertext
    We'll store: base64(nonce + tag + ciphertext)
    """
    if plaintext is None:
        return None
    key = get_encryption_key()
    cipher = AES.new(key, AES.MODE_GCM)
    nonce = cipher.nonce  # 12 bytes usually
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    blob = nonce + tag + ciphertext
    return base64.b64encode(blob).decode("utf-8")

def decrypt_text(token: str) -> str:
    """
    Decrypt the stored base64 string created by encrypt_text.
    """
    if token is None:
        return None
    key = get_encryption_key()
    blob = base64.b64decode(token)
    # nonce (12) + tag (16) + ciphertext
    nonce = blob[:12]
    tag = blob[12:28]
    ciphertext = blob[28:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode("utf-8")

