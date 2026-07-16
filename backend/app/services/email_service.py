import logging
import smtplib
from collections.abc import Iterable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from_email)


def send_email(
    to: str, subject: str, html_body: str, text_body: str | None = None
) -> bool:
    smtp_host = settings.smtp_host
    smtp_from_email = settings.smtp_from_email
    if not smtp_host or not smtp_from_email:
        logger.info("SMTP not configured; skipping email to %s: %s", to, subject)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from_email
        msg["To"] = to
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(smtp_host, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(smtp_from_email, [to], msg.as_string())
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


def notify_users_announcement(
    recipients: Iterable[str],
    announcement: str,
    admin_name: str,
) -> int:
    sent = 0
    subject = f"Nexora Update from {admin_name}"
    text = f"{admin_name} posted a new announcement:\n\n{announcement}\n\nVisit {settings.public_app_url}"
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#059669;">Nexora Announcement</h2>
      <p><strong>{admin_name}</strong> posted a new update:</p>
      <div style="background:#f3f4f6;padding:16px;border-radius:8px;margin:16px 0;">
        {announcement.replace(chr(10), "<br>")}
      </div>
      <p><a href="{settings.public_app_url}">Open Nexora</a></p>
    </div>
    """
    for email in recipients:
        if email and send_email(email, subject, html, text):
            sent += 1
    return sent
