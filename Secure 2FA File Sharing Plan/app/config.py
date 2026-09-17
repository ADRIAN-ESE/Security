"""Application configuration.

Secrets resolution order:
  1. Environment variable (production / Docker)
  2. Auto-generated value persisted under storage/ (local development)
"""

import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)


def _persistent_secret(env_name: str, file_name: str, generator) -> str:
    """Return a secret from the environment, or create/persist one locally."""
    value = os.environ.get(env_name)
    if value:
        return value
    secret_file = STORAGE_DIR / file_name
    if secret_file.exists():
        return secret_file.read_text().strip()
    value = generator()
    secret_file.write_text(value)
    return value


class Config:
    SECRET_KEY = _persistent_secret("SECRET_KEY", "secret.key", lambda: secrets.token_hex(32))
    MASTER_KEY = _persistent_secret("MASTER_KEY", "master.key", lambda: Fernet.generate_key().decode())

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"
    SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "secure_share_session")

    WTF_CSRF_TIME_LIMIT = None  # CSRF tokens valid for the whole session

    ALLOWED_UPLOAD_EXTENSIONS = {
        ".pdf", ".txt", ".csv", ".json", ".md", ".png", ".jpg", ".jpeg",
        ".gif", ".webp", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".zip", ".tar", ".gz", ".bz2", ".rar"
    }
    ALLOWED_UPLOAD_MIME_TYPES = {
        "application/pdf", "text/plain", "text/csv", "application/json",
        "text/markdown", "image/png", "image/jpeg", "image/gif", "image/webp",
        "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip", "application/x-zip-compressed", "application/gzip"
    }

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "1") == "1"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@secure-share.local")
    MAIL_DEBUG = os.environ.get("MAIL_DEBUG", "0") == "1"
