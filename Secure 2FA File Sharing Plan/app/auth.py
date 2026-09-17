"""Authentication blueprint: register, login, logout, TOTP 2FA, recovery codes."""

import base64
import hashlib
import io
import re
import secrets

import bcrypt
import pyotp
import qrcode
from flask import (
    Blueprint, abort, flash, redirect, render_template, request, session, url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from crypto_utils import decrypt_str, encrypt_str
from extensions import limiter
from models import File, RecoveryCode, ShareLink, User, db
from notifications import send_email

auth_bp = Blueprint("auth", __name__)


def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*()\[\]{}_\-+=~`|\\:;\"'<>?,./]", password):
        return False
    return True


def validate_email(email: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email))


def _hash_recovery(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("files.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("files.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
        elif len(username) > 80 or len(email) > 255:
            flash("Username or email is too long.", "error")
        elif not validate_email(email):
            flash("Please enter a valid email address.", "error")
        elif not validate_password(password):
            flash(
                "Password must be at least 8 characters and include uppercase, lowercase, a number, and a special character.",
                "error",
            )
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif User.query.filter_by(username=username).first():
            flash("That username is already registered.", "error")
        else:
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user = User(username=username, email=email, password_hash=pw_hash)
            db.session.add(user)
            db.session.commit()
            send_email(
                subject="Welcome to SecureShare",
                to=user.email,
                body=(
                    f"Hi {user.username},\n\nYour SecureShare account is ready. "
                    "Complete 2FA setup to protect your files."
                ),
            )
            login_user(user)
            flash("Account created! Now secure it with two-factor authentication.", "success")
            return redirect(url_for("auth.setup_2fa"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("files.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        # Factor 1: password
        if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            if user.is_2fa_enabled:
                # Do NOT log in yet — park a pre-2FA flag and demand factor 2.
                session["pre_2fa_user_id"] = user.id
                return redirect(url_for("auth.verify_2fa"))
            login_user(user)
            return redirect(url_for("files.dashboard"))
        flash("Invalid username or password.", "error")

    return render_template("login.html")


@auth_bp.route("/verify-2fa", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def verify_2fa():
    user_id = session.get("pre_2fa_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    user = db.session.get(User, user_id)
    if not user or not user.is_2fa_enabled:
        session.pop("pre_2fa_user_id", None)
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        code = request.form.get("code", "").replace(" ", "").replace("-", "")
        ok = False

        # Factor 2: TOTP code from the authenticator app
        if len(code) == 6 and code.isdigit():
            secret = decrypt_str(user.totp_secret_enc)
            ok = pyotp.TOTP(secret).verify(code, valid_window=1)

        # Fallback: one-time recovery code
        if not ok:
            rc = RecoveryCode.query.filter_by(
                user_id=user.id, code_hash=_hash_recovery(code), used=False
            ).first()
            if rc:
                rc.used = True
                db.session.commit()
                ok = True
                flash("Signed in with a recovery code — that code is now used up.", "success")

        if ok:
            session.pop("pre_2fa_user_id", None)
            login_user(user)
            return redirect(url_for("files.dashboard"))
        flash("Invalid code. Try again.", "error")

    return render_template("verify_2fa.html")


@auth_bp.route("/setup-2fa", methods=["GET", "POST"])
@login_required
def setup_2fa():
    if current_user.is_2fa_enabled:
        flash("Two-factor authentication is already enabled on your account.", "success")
        return redirect(url_for("files.dashboard"))

    if request.method == "POST":
        pending = session.get("pending_totp_secret")
        code = request.form.get("code", "").replace(" ", "")
        if pending and pyotp.TOTP(pending).verify(code, valid_window=1):
            # Secret verified -> store it ENCRYPTED and enable 2FA.
            current_user.totp_secret_enc = encrypt_str(pending)
            current_user.is_2fa_enabled = True

            # Issue 10 one-time recovery codes (only hashes are stored).
            RecoveryCode.query.filter_by(user_id=current_user.id).delete()
            codes = []
            for _ in range(10):
                c = f"{secrets.token_hex(2)}-{secrets.token_hex(2)}"
                codes.append(c)
                # Hash the normalized form (dash stripped) to match verification.
                db.session.add(
                    RecoveryCode(
                        user_id=current_user.id,
                        code_hash=_hash_recovery(c.replace("-", "")),
                    )
                )
            db.session.commit()
            session.pop("pending_totp_secret", None)
            return render_template("recovery_codes.html", codes=codes)
        flash("Invalid code — check your authenticator app and try again.", "error")

    if "pending_totp_secret" not in session:
        session["pending_totp_secret"] = pyotp.random_base32()
    secret = session["pending_totp_secret"]

    uri = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.username, issuer_name="SecureShare"
    )
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render_template("setup_2fa.html", qr_b64=qr_b64, secret=secret)


@auth_bp.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)

    user_count = User.query.count()
    file_count = File.query.count()
    share_count = ShareLink.query.count()
    active_share_count = sum(1 for link in ShareLink.query.all() if link.is_valid())
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_files = File.query.order_by(File.uploaded_at.desc()).limit(5).all()

    return render_template(
        "admin_dashboard.html",
        user_count=user_count,
        file_count=file_count,
        share_count=share_count,
        active_share_count=active_share_count,
        recent_users=recent_users,
        recent_files=recent_files,
    )


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
