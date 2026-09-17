"""File blueprint: encrypted upload/download/delete + share-link management."""

import io
import mimetypes
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import (
    Blueprint, abort, flash, redirect, render_template, request, send_file, url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from config import STORAGE_DIR
from crypto_utils import decrypt_bytes, encrypt_bytes
from models import File, ShareLink, db

files_bp = Blueprint("files", __name__)


def validate_uploaded_file(filename: str, mime_type: str | None, data: bytes) -> tuple[bool, str | None]:
    """Allow only business-safe document and media uploads; reject suspicious file types."""
    safe_name = secure_filename(filename or "")
    if not safe_name or "." not in safe_name:
        return False, "File type is not allowed. Use a standard document or media file."

    ext = Path(safe_name).suffix.lower()
    allowed_exts = {".pdf", ".txt", ".csv", ".json", ".md", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".tar", ".gz", ".bz2", ".rar"}
    if ext not in allowed_exts:
        return False, f"File extension '{ext or 'unknown'}' is not allowed."

    guessed_type, _ = mimetypes.guess_type(safe_name)
    normalized = (mime_type or "").split(";", 1)[0].strip().lower()
    allowed_mimes = {"application/pdf", "text/plain", "text/csv", "application/json", "text/markdown", "image/png", "image/jpeg", "image/gif", "image/webp", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/zip", "application/x-zip-compressed", "application/gzip"}
    if normalized and normalized not in allowed_mimes:
        return False, f"File type '{normalized}' is not allowed."
    if guessed_type and guessed_type not in allowed_mimes:
        return False, f"File type '{guessed_type}' is not allowed."

    dangerous_signatures = [b"MZ", b"PK\x03\x04", b"#!/", b"<script", b"<?php"]
    if any(sig in data[:128].upper() for sig in dangerous_signatures):
        return False, "This file type is not allowed for upload."

    return True, None


def parse_share_expiry(expiry: str | None) -> timedelta | None:
    """Return a TTL for a share link or None when the link should never expire."""
    value = (expiry or "").strip().lower()
    if not value or value == "never":
        return None
    return _EXPIRY_CHOICES.get(value)


@files_bp.app_template_filter("humansize")
def humansize(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def _owned_file(file_id: int) -> File:
    rec = db.session.get(File, file_id)
    if not rec or rec.owner_id != current_user.id:
        abort(404)  # don't reveal that the file exists
    return rec


@files_bp.route("/dashboard")
@login_required
def dashboard():
    files = (
        File.query.filter_by(owner_id=current_user.id)
        .order_by(File.uploaded_at.desc())
        .all()
    )
    total_size = sum(file.size for file in files)
    return render_template(
        "dashboard.html",
        files=files,
        total_files=len(files),
        total_size=total_size,
    )


@files_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    f = request.files.get("file")
    if not f or not f.filename:
        flash("No file selected.", "error")
        return redirect(url_for("files.dashboard"))

    data = f.read()
    if not data:
        flash("Cannot upload an empty file.", "error")
        return redirect(url_for("files.dashboard"))

    ok, message = validate_uploaded_file(f.filename, f.mimetype, data)
    if not ok:
        flash(message or "File type is not allowed.", "error")
        return redirect(url_for("files.dashboard"))

    stored_name = uuid.uuid4().hex
    (STORAGE_DIR / stored_name).write_bytes(encrypt_bytes(data))

    rec = File(
        owner_id=current_user.id,
        original_filename=secure_filename(f.filename) or "file",
        stored_filename=stored_name,
        size=len(data),
    )
    db.session.add(rec)
    db.session.commit()
    flash(f"Uploaded and encrypted: {rec.original_filename}", "success")
    return redirect(url_for("files.dashboard"))


@files_bp.route("/download/<int:file_id>")
@login_required
def download(file_id):
    rec = _owned_file(file_id)
    path = STORAGE_DIR / rec.stored_filename
    if not path.exists():
        abort(404)
    plaintext = decrypt_bytes(path.read_bytes())
    return send_file(
        io.BytesIO(plaintext), as_attachment=True, download_name=rec.original_filename
    )


@files_bp.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete(file_id):
    rec = _owned_file(file_id)
    path = STORAGE_DIR / rec.stored_filename
    path.unlink(missing_ok=True)
    db.session.delete(rec)
    db.session.commit()
    flash(f"Deleted {rec.original_filename}.", "success")
    return redirect(url_for("files.dashboard"))


# ------------------------------ sharing ---------------------------------

_EXPIRY_CHOICES = {
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
    "7d": timedelta(days=7),
}


@files_bp.route("/shares")
@login_required
def shares():
    links = (
        ShareLink.query.join(File)
        .filter(File.owner_id == current_user.id)
        .order_by(ShareLink.created_at.desc())
        .all()
    )
    files = File.query.filter_by(owner_id=current_user.id).order_by(File.uploaded_at.desc()).all()
    return render_template("shares.html", links=links, files=files)


@files_bp.route("/share/create", methods=["POST"])
@login_required
def create_share():
    rec = _owned_file(int(request.form.get("file_id", "0")))

    delta = parse_share_expiry(request.form.get("expiry"))
    expires_at = datetime.now(timezone.utc) + delta if delta else None

    md = (request.form.get("max_downloads") or "").strip()
    max_downloads = int(md) if md.isdigit() and int(md) > 0 else None
    if max_downloads is not None and max_downloads > 25:
        flash("Maximum downloads per share link is 25 for safety.", "error")
        return redirect(url_for("files.shares"))

    link = ShareLink(
        file_id=rec.id,
        token=secrets.token_urlsafe(32),
        expires_at=expires_at,
        max_downloads=max_downloads,
    )
    db.session.add(link)
    db.session.commit()
    flash("Share link created.", "success")
    return redirect(url_for("files.shares"))


@files_bp.route("/share/revoke/<int:link_id>", methods=["POST"])
@login_required
def revoke_share(link_id):
    link = db.session.get(ShareLink, link_id)
    if not link or link.file.owner_id != current_user.id:
        abort(404)
    link.revoked = True
    db.session.commit()
    flash("Share link revoked.", "success")
    return redirect(url_for("files.shares"))


@files_bp.route("/s/<token>")
def public_download(token):
    """Public, unauthenticated download via a share token. Fails closed."""
    link = ShareLink.query.filter_by(token=token).first()
    if not link or not link.is_valid():
        return (
            render_template(
                "error.html",
                message="This share link is invalid, expired, revoked, or has "
                "reached its download limit.",
            ),
            410,
        )

    path = STORAGE_DIR / link.file.stored_filename
    if not path.exists():
        return render_template("error.html", message="File no longer exists."), 410

    link.download_count += 1
    db.session.commit()

    plaintext = decrypt_bytes(path.read_bytes())
    return send_file(
        io.BytesIO(plaintext),
        as_attachment=True,
        download_name=link.file.original_filename,
    )
