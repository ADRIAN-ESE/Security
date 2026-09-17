"""Encryption helpers.

All files are encrypted with Fernet (AES-128-CBC under the hood with HMAC
authentication) before they touch disk, and TOTP secrets are encrypted before
being stored in the database. The master key lives outside the codebase
(environment variable or storage/master.key, which is gitignored).
"""

from cryptography.fernet import Fernet

_fernet: Fernet | None = None


def init_crypto(key: str | bytes) -> None:
    global _fernet
    _fernet = Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_bytes(data: bytes) -> bytes:
    return _fernet.encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    return _fernet.decrypt(token)


def encrypt_str(text: str) -> str:
    return _fernet.encrypt(text.encode()).decode()


def decrypt_str(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()
