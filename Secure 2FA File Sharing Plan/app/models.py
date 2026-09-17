"""SQLAlchemy models: User, RecoveryCode, File, ShareLink."""

from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect

db = SQLAlchemy()


def migrate_user_email_uniqueness() -> None:
    if db.engine.dialect.name != "sqlite":
        return

    inspector = inspect(db.engine)
    if not any(
        set(constraint["column_names"]) == {"email"}
        for constraint in inspector.get_unique_constraints("users")
    ):
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("users")
    }
    columns = [
        "id",
        "username",
        "email",
        "password_hash",
        "totp_secret_enc",
        "is_2fa_enabled",
        "is_admin",
        "created_at",
    ]
    expressions = [
        column if column in existing_columns else ("0" if column in {"is_2fa_enabled", "is_admin"} else "NULL")
        for column in columns
    ]

    with db.engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("ALTER TABLE users RENAME TO users_old")
        connection.exec_driver_sql(
            """
            CREATE TABLE users (
                id INTEGER NOT NULL,
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                totp_secret_enc TEXT,
                is_2fa_enabled BOOLEAN NOT NULL DEFAULT 0,
                is_admin BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME,
                PRIMARY KEY (id)
            )
            """
        )
        connection.exec_driver_sql(
            f"INSERT INTO users ({', '.join(columns)}) SELECT {', '.join(expressions)} FROM users_old"
        )
        connection.exec_driver_sql("DROP TABLE users_old")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # TOTP secret is stored ENCRYPTED with the master key, never in plaintext.
    totp_secret_enc = db.Column(db.Text, nullable=True)
    is_2fa_enabled = db.Column(db.Boolean, nullable=False, default=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    files = db.relationship("File", backref="owner", lazy=True, cascade="all, delete-orphan")
    recovery_codes = db.relationship(
        "RecoveryCode", backref="user", lazy=True, cascade="all, delete-orphan"
    )


class RecoveryCode(db.Model):
    """One-time backup codes for 2FA. Only the SHA-256 hash is stored."""

    __tablename__ = "recovery_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    code_hash = db.Column(db.String(64), nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)


class File(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(64), nullable=False)  # random UUID on disk
    size = db.Column(db.Integer, nullable=False)  # plaintext size in bytes
    uploaded_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    share_links = db.relationship(
        "ShareLink", backref="file", lazy=True, cascade="all, delete-orphan"
    )


class ShareLink(db.Model):
    __tablename__ = "share_links"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)  # NULL = never
    max_downloads = db.Column(db.Integer, nullable=True)  # NULL = unlimited
    download_count = db.Column(db.Integer, nullable=False, default=0)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def is_valid(self) -> bool:
        """Fail-closed validity check: revoked, expired, or exhausted -> False."""
        if self.revoked:
            return False
        if self.expires_at is not None:
            exp = self.expires_at
            if exp.tzinfo is None:  # SQLite returns naive datetimes
                exp = exp.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp:
                return False
        if self.max_downloads is not None and self.download_count >= self.max_downloads:
            return False
        return True

    def status(self) -> str:
        if self.revoked:
            return "Revoked"
        if self.expires_at is not None:
            exp = self.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp:
                return "Expired"
        if self.max_downloads is not None and self.download_count >= self.max_downloads:
            return "Limit reached"
        return "Active"
