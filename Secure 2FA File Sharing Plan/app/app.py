"""SecureShare — secure file sharing with TOTP two-factor authentication.

Run locally:  python app.py            (http://localhost:8000)
In Docker:    see Dockerfile           (PORT env var, default 8000)
"""

import os

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template

from config import Config
from crypto_utils import init_crypto
from extensions import csrf, limiter, login_manager
from models import User, db, migrate_user_email_uniqueness


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)
    limiter.init_app(app)
    init_crypto(app.config["MASTER_KEY"])

    from auth import auth_bp
    from files import files_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.after_request
    def security_headers(resp):
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'; "
            "object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
        )
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "same-origin"
        resp.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        resp.headers["X-Download-Options"] = "noopen"
        return resp

    @app.route("/health")
    def health_check():
        return {"status": "ok", "app": "SecureShare"}, 200

    @app.errorhandler(413)
    def too_large(_e):
        return render_template("error.html", message="File too large (100 MB max)."), 413

    @app.errorhandler(429)
    def rate_limited(_e):
        return (
            render_template(
                "error.html", message="Too many attempts. Wait a minute and try again."
            ),
            429,
        )

    with app.app_context():
        migrate_user_email_uniqueness()
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
