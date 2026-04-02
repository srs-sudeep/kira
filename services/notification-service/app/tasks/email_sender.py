"""Celery tasks for notification-service email delivery.

All tasks use SendGrid when SENDGRID_API_KEY is set; otherwise they log the
email contents so local development works without any external dependencies.

Retry strategy: 3 attempts with 60-second delay between each.
"""
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


@celery_app.task(
    bind=True,
    name="app.tasks.email_sender.send_new_booking_alert",
    max_retries=3,
    default_retry_delay=60,
)
def send_new_booking_alert(
    self,
    to_email: str,
    recipient_name: str,
    confirmation_number: str,
    guest_name: str,
    check_in: str,
    check_out: str,
    room_type: str,
    total_amount: str,
    currency: str,
) -> None:
    try:
        html = f"""
        <h2>New Booking Alert</h2>
        <p>Hi {recipient_name},</p>
        <p>A new reservation has been confirmed.</p>
        <table>
          <tr><td><strong>Confirmation #</strong></td><td>{confirmation_number}</td></tr>
          <tr><td><strong>Guest</strong></td><td>{guest_name}</td></tr>
          <tr><td><strong>Check-in</strong></td><td>{check_in}</td></tr>
          <tr><td><strong>Check-out</strong></td><td>{check_out}</td></tr>
          <tr><td><strong>Room</strong></td><td>{room_type}</td></tr>
          <tr><td><strong>Total</strong></td><td>{currency} {total_amount}</td></tr>
        </table>
        """
        _send_or_log(to_email, f"New Booking: {confirmation_number}", html)
    except Exception as exc:
        logger.warning("send_new_booking_alert_failed", exc=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.tasks.email_sender.send_cancellation_alert",
    max_retries=3,
    default_retry_delay=60,
)
def send_cancellation_alert(
    self,
    to_email: str,
    recipient_name: str,
    confirmation_number: str,
    guest_name: str,
    cancellation_reason: str,
) -> None:
    try:
        html = f"""
        <h2>Reservation Cancelled</h2>
        <p>Hi {recipient_name},</p>
        <p>Reservation <strong>{confirmation_number}</strong> for guest <strong>{guest_name}</strong> has been cancelled.</p>
        <p><strong>Reason:</strong> {cancellation_reason}</p>
        """
        _send_or_log(to_email, f"Cancellation: {confirmation_number}", html)
    except Exception as exc:
        logger.warning("send_cancellation_alert_failed", exc=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.tasks.email_sender.send_channel_failure_alert",
    max_retries=3,
    default_retry_delay=60,
)
def send_channel_failure_alert(
    self,
    to_email: str,
    recipient_name: str,
    channel_name: str,
    ota_code: str,
    error_message: str,
) -> None:
    try:
        html = f"""
        <h2>Channel Sync Failure</h2>
        <p>Hi {recipient_name},</p>
        <p>The channel <strong>{channel_name}</strong> ({ota_code}) has encountered a sync error.</p>
        <p><strong>Error:</strong> {error_message}</p>
        <p>Please review the channel settings and reconnect if necessary.</p>
        """
        _send_or_log(to_email, f"Channel Failure: {channel_name}", html)
    except Exception as exc:
        logger.warning("send_channel_failure_alert_failed", exc=str(exc))
        raise self.retry(exc=exc)
