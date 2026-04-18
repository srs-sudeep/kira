"""Celery tasks for transactional email delivery (SendGrid / Mailhog fallback)."""

import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import settings
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _send_or_log(to_email: str, subject: str, html_content: str) -> None:
    """Send via SendGrid when the API key is configured; log otherwise (dev/test)."""
    if not settings.SENDGRID_API_KEY:
        logger.info(
            "email_skipped_no_api_key",
            to=to_email,
            subject=subject,
        )
        return

    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = sg.send(message)
    logger.info("email_sent", to=to_email, subject=subject, status=response.status_code)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_invite_email(
    self,
    to_email: str,
    first_name: str,
    temp_password: str,
    tenant_name: str,
) -> None:
    """Send an account-invitation email with a temporary password."""
    try:
        html = f"""
        <h2>Welcome to KIRA Hotel Manager, {first_name}!</h2>
        <p>You have been invited to join <strong>{tenant_name}</strong>.</p>
        <p>Your temporary password is: <code>{temp_password}</code></p>
        <p>Please log in and change it immediately.</p>
        """
        _send_or_log(to_email, "You have been invited to KIRA Hotel Manager", html)
    except Exception as exc:
        logger.warning("send_invite_email_failed", to=to_email, exc=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, to_email: str, first_name: str, reset_link: str) -> None:
    """Send a password-reset link."""
    try:
        html = f"""
        <h2>Password Reset Request</h2>
        <p>Hi {first_name},</p>
        <p>Click the link below to reset your KIRA password. It expires in 30 minutes.</p>
        <p><a href="{reset_link}">Reset my password</a></p>
        <p>If you did not request this, please ignore this email.</p>
        """
        _send_or_log(to_email, "Reset your KIRA password", html)
    except Exception as exc:
        logger.warning("send_password_reset_email_failed", to=to_email, exc=str(exc))
        raise self.retry(exc=exc)
