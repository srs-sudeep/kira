---
sidebar_position: 5
---

# Notification Service

Manages all outbound communications — email and in-app alerts. Runs on port **8005**.

## Responsibilities

- Send transactional emails via SendGrid (booking confirmations, cancellations, sync failure alerts)
- Create and serve in-app notifications in the dashboard
- Provide a notification archive with read/unread state and bulk actions
- Per-user notification preferences (email vs. in-app per event type)
- Consume Kafka events to trigger notifications automatically

## Key Endpoints

### Notifications

| Method | Path | Description |
|---|---|---|
| `GET` | `/notifications/` | List notifications (filters: type, is_read) |
| `GET` | `/notifications/unread-count` | Get unread count |
| `POST` | `/notifications/{id}/read` | Mark as read |
| `POST` | `/notifications/read-all` | Mark all as read |
| `DELETE` | `/notifications/{id}` | Delete notification |
| `POST` | `/notifications/bulk-action` | Bulk mark-read or delete |

### Preferences

| Method | Path | Description |
|---|---|---|
| `GET` | `/notifications/preferences` | Get user preferences |
| `PATCH` | `/notifications/preferences` | Update preferences |

## Kafka Events Consumed

### `reservation.created` → Booking Confirmation Email

```python
@kafka_consumer.on("reservation.created")
async def handle_reservation_created(event: dict):
    if await should_notify(event["tenant_id"], "email", "reservation.created"):
        await email_service.send_booking_confirmation(
            to=event["guest_email"],
            reservation_data=event,
        )
    await notification_repo.create(
        tenant_id=event["tenant_id"],
        type=NotificationType.RESERVATION_CREATED,
        title="New booking confirmed",
        body=f"Booking #{event['reservation_id'][:8]} for {event['check_in']}",
        metadata=event,
    )
```

### `reservation.cancelled` → Cancellation Notice

Sends cancellation email to guest and creates in-app alert for property manager.

### `channel.sync.failed` → Sync Failure Alert

Creates an in-app notification with the error details so the manager can investigate.

## Data Models

### Notification

```python
class Notification(Base):
    id: UUID
    tenant_id: UUID
    user_id: UUID | None      # None = broadcast to all hotel_admin+
    type: NotificationType    # reservation_created | reservation_cancelled | sync_failed | system
    title: str
    body: str
    is_read: bool
    metadata: dict            # JSONB — original event payload
    created_at: datetime
    read_at: datetime | None
```

### NotificationPreferences

```python
class NotificationPreferences(Base):
    user_id: UUID
    # Reservation events
    reservation_created_email: bool = True
    reservation_created_in_app: bool = True
    reservation_cancelled_email: bool = True
    reservation_cancelled_in_app: bool = True
    # Channel events
    sync_failed_email: bool = True
    sync_failed_in_app: bool = True
    # System
    system_email: bool = True
    system_in_app: bool = True
```

## Email Templates

Templates are Jinja2 HTML files in `app/templates/email/`:

- `booking_confirmation.html` — guest booking confirmation
- `cancellation_notice.html` — guest cancellation receipt
- `sync_failure_alert.html` — internal alert for property managers
- `invite_user.html` — new user invitation
- `mfa_backup_codes.html` — MFA backup codes delivery

## Configuration

```python
class Settings(BaseSettings):
    SMTP_HOST: str            # smtp.sendgrid.net
    SMTP_PORT: int = 587
    SMTP_USER: str            # "apikey"
    SMTP_PASSWORD: str        # SendGrid API key
    EMAIL_FROM: str           # noreply@kira.abodeab.com
    EMAIL_FROM_NAME: str = "KIRA Platform"
```
