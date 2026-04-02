---
sidebar_position: 4
---

# Channel Engine

The integration layer connecting KIRA to OTAs. Runs on port **8004** (API) with a separate Celery worker pod.

## Responsibilities

- OTA adapter implementations for Booking.com, Expedia, MakeMyTrip
- Push ARI updates to connected OTAs
- Pull new reservations from OTAs on schedule and via webhooks
- Retry failed syncs with exponential backoff
- Circuit breaker to isolate failing OTAs
- Sync log for observability

## Architecture

```
Kafka ari.updated
       │
       ▼
 Celery Worker ──► OTA Adapter ──► Booking.com API
                              ──► Expedia EQC
                              ──► MakeMyTrip API

Scheduler (beat) ──► Pull reservations from OTAs
                 ──► Health check OTA connections
```

## Key Endpoints

### Channels

| Method | Path | Description |
|---|---|---|
| `GET` | `/channels/` | List connected channels |
| `POST` | `/channels/` | Connect a new OTA channel |
| `GET` | `/channels/{id}` | Channel details + status |
| `PATCH` | `/channels/{id}` | Update channel credentials/config |
| `DELETE` | `/channels/{id}` | Disconnect channel |
| `POST` | `/channels/{id}/test` | Test OTA connection |
| `POST` | `/channels/{id}/sync-now` | Trigger immediate full ARI push |

### Mappings

| Method | Path | Description |
|---|---|---|
| `GET` | `/channels/{id}/mappings` | List room type / rate plan mappings |
| `POST` | `/channels/{id}/mappings` | Create mapping |
| `PATCH` | `/channels/{id}/mappings/{mapping_id}` | Update mapping |
| `DELETE` | `/channels/{id}/mappings/{mapping_id}` | Remove mapping |

### Sync Log

| Method | Path | Description |
|---|---|---|
| `GET` | `/channels/{id}/sync-log` | Paginated sync history |

## OTA Adapter Interface

All OTA adapters implement the same abstract interface:

```python
class BaseOTAAdapter(ABC):
    @abstractmethod
    async def push_ari(
        self,
        channel: Channel,
        mappings: list[ChannelMapping],
        ari_data: list[ARICalendarEntry],
    ) -> SyncResult:
        ...

    @abstractmethod
    async def pull_reservations(
        self,
        channel: Channel,
        from_date: date,
        to_date: date,
    ) -> list[ReservationPayload]:
        ...

    @abstractmethod
    async def test_connection(self, channel: Channel) -> bool:
        ...
```

## Sync Retry Strategy

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # seconds
)
def push_ari_to_channel(self, channel_id: str, ari_event: dict):
    try:
        adapter = get_adapter(channel_id)
        result = adapter.push_ari(...)
        log_sync(channel_id, "success", result)
    except OTATemporaryError as exc:
        # Exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    except OTAPermanentError as exc:
        log_sync(channel_id, "failed", str(exc))
        publish_sync_failed_event(channel_id, exc)
        # Don't retry permanent errors
```

## Circuit Breaker

The circuit breaker prevents hammering an OTA that's down:

- **Closed** (normal) → requests pass through
- **Open** → OTA errored too many times, requests fail fast for 5 minutes
- **Half-open** → one test request every 5 minutes to check recovery

Circuit breaker state is stored in Redis per (tenant_id, channel) pair.

## Celery Beat Schedule

```python
CELERYBEAT_SCHEDULE = {
    "pull-reservations-every-15min": {
        "task": "app.tasks.pull_reservations_all_channels",
        "schedule": crontab(minute="*/15"),
    },
    "health-check-channels-hourly": {
        "task": "app.tasks.health_check_all_channels",
        "schedule": crontab(minute=0),
    },
}
```

## Data Models

### Channel

```python
class Channel(Base):
    id: UUID
    name: str                 # e.g., "Booking.com - Grand Hotel"
    ota: OTAType              # booking_com | expedia | mmt
    credentials: dict         # encrypted JSONB
    is_active: bool
    last_sync_at: datetime | None
    sync_status: SyncStatus   # active | error | paused
    error_message: str | None
```

### ChannelMapping

```python
class ChannelMapping(Base):
    id: UUID
    channel_id: UUID
    room_type_id: UUID        # KIRA room type
    rate_plan_id: UUID        # KIRA rate plan
    ota_room_id: str          # OTA's room type identifier
    ota_rate_id: str          # OTA's rate plan identifier
    is_active: bool
```
