from __future__ import annotations

import base64
from hashlib import sha256

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet() -> Fernet:
    key = settings.FERNET_KEY
    if not key:
        key = base64.urlsafe_b64encode(sha256(settings.SECRET_KEY.encode()).digest()).decode()
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_token(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_token(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Invalid or corrupted token") from e
