import os
from email.message import EmailMessage
from smtplib import SMTP


def send_email(subject: str, to: str, body: str) -> bool:
    """Send a simple notification email when mail configuration is present."""
    server = os.environ.get("MAIL_SERVER")
    if not server:
        return False

    sender = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@secure-share.local")
    port = int(os.environ.get("MAIL_PORT", "587"))
    username = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(body)

    try:
        with SMTP(server, port) as smtp:
            if os.environ.get("MAIL_USE_TLS", "1") == "1":
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
        return True
    except Exception:
        return False
