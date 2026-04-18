"""Celery tasks for reservation transactional emails."""

import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import settings
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _send_or_log(to_email: str, subject: str, html: str) -> None:
    if not settings.sendgrid_api_key:
        logger.info("email_skipped_no_api_key", to=to_email, subject=subject)
        return
    sg = SendGridAPIClient(settings.sendgrid_api_key)
    msg = Mail(
        from_email=settings.from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html,
    )
    resp = sg.send(msg)
    logger.info("email_sent", to=to_email, status=resp.status_code)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation(
    self,
    to_email: str,
    guest_name: str,
    confirmation_number: str,
    hotel_name: str,
    check_in: str,
    check_out: str,
    nights: int,
    total_amount: str,
    currency: str,
) -> None:
    try:
        html = f"""
        <h2>Booking Confirmed — {hotel_name}</h2>
        <p>Dear {guest_name},</p>
        <p>Your reservation has been confirmed.</p>
        <table>
          <tr><td><strong>Confirmation #</strong></td><td>{confirmation_number}</td></tr>
          <tr><td><strong>Check-in</strong></td><td>{check_in}</td></tr>
          <tr><td><strong>Check-out</strong></td><td>{check_out}</td></tr>
          <tr><td><strong>Nights</strong></td><td>{nights}</td></tr>
          <tr><td><strong>Total</strong></td><td>{currency} {total_amount}</td></tr>
        </table>
        <p>We look forward to welcoming you!</p>
        """
        _send_or_log(to_email, f"Booking Confirmed: {confirmation_number}", html)
    except Exception as exc:
        logger.warning("send_booking_confirmation_failed", exc=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_cancellation_notice(
    self,
    to_email: str,
    guest_name: str,
    confirmation_number: str,
    reason: str,
) -> None:
    try:
        html = f"""
        <h2>Reservation Cancelled</h2>
        <p>Dear {guest_name},</p>
        <p>Your reservation <strong>{confirmation_number}</strong> has been cancelled.</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p>If you have any questions, please contact the hotel directly.</p>
        """
        _send_or_log(to_email, f"Cancellation Notice: {confirmation_number}", html)
    except Exception as exc:
        logger.warning("send_cancellation_notice_failed", exc=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_modification_notice(
    self,
    to_email: str,
    guest_name: str,
    confirmation_number: str,
    changes: str,
) -> None:
    try:
        html = f"""
        <h2>Reservation Modified</h2>
        <p>Dear {guest_name},</p>
        <p>Your reservation <strong>{confirmation_number}</strong> has been updated.</p>
        <p><strong>Changes:</strong> {changes}</p>
        """
        _send_or_log(to_email, f"Reservation Modified: {confirmation_number}", html)
    except Exception as exc:
        logger.warning("send_modification_notice_failed", exc=str(exc))
        raise self.retry(exc=exc)
