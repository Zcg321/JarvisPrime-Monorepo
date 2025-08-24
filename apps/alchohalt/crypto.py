from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


@lru_cache()
def get_fernet() -> Optional[Fernet]:
    key = os.getenv("ALC_CRYPTO_KEY")
    if not key:
        return None
    try:
        return Fernet(key)
    except Exception:
        return None


def encryption_enabled() -> bool:
    return get_fernet() is not None


def encrypt_note(note: Optional[str]) -> Optional[str]:
    if not note:
        return note
    f = get_fernet()
    if not f:
        return note
    token = f.encrypt(note.encode()).decode()
    return f"enc:{token}"


def decrypt_note(note: Optional[str]) -> Optional[str]:
    if not note:
        return note
    if not note.startswith("enc:"):
        return note
    f = get_fernet()
    if not f:
        return None
    try:
        return f.decrypt(note[4:].encode()).decode()
    except InvalidToken:
        return None


def is_encrypted(note: Optional[str]) -> bool:
    return bool(note and note.startswith("enc:"))
