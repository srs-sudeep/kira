---
sidebar_position: 3
---

# Reservation Service

Handles the full booking lifecycle — creation, modification, and cancellation. Runs on port **8003**.

## Responsibilities

- Record reservations from OTAs and direct channels
- Store guest profiles with stay history
- Handle booking modifications (dates, rooms, rate plans)
- Apply cancellation policies and calculate refunds
- Publish `reservation.created` and `reservation.cancelled` Kafka events

## Key Endpoints

### Reservations

| Method | Path | Description |
|---|---|---|
| `GET` | `/reservations/` | List reservations (filters: status, channel, date range) |
| `POST` | `/reservations/` | Create reservation |
| `GET` | `/reservations/{id}` | Get reservation details |
| `PATCH` | `/reservations/{id}` | Modify reservation |
| `POST` | `/reservations/{id}/cancel` | Cancel reservation |
| `POST` | `/reservations/{id}/check-in` | Mark as checked in |
| `POST` | `/reservations/{id}/check-out` | Mark as checked out |

### Guests

| Method | Path | Description |
|---|---|---|
| `GET` | `/guests/` | List guests |
| `GET` | `/guests/{id}` | Guest profile + stay history |
| `PATCH` | `/guests/{id}` | Update guest profile |

## Data Models

### Reservation

```python
class Reservation(Base):
    id: UUID
    confirmation_number: str  # e.g., "KIRA-2025-00001"
    channel: BookingChannel   # direct | booking_com | expedia | mmt
    channel_confirmation_id: str | None  # OTA's reference number
    guest_id: UUID
    room_type_id: UUID
    rate_plan_id: UUID
    check_in: date
    check_out: date
    nights: int               # computed
    adults: int
    children: int
    room_rate: Decimal        # per night at booking time
    total_amount: Decimal
    currency: str
    status: ReservationStatus # confirmed | checked_in | checked_out | cancelled | no_show
    special_requests: str | None
    created_at: datetime
    modified_at: datetime
    cancelled_at: datetime | None
    cancellation_reason: str | None
    refund_amount: Decimal | None
```

### Guest

```python
class Guest(Base):
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: str | None
    country: str | None
    date_of_birth: date | None
    id_type: str | None       # passport | national_id
    id_number: str | None
    created_at: datetime
    total_stays: int          # computed from reservations
```

## Cancellation Policy Enforcement

When cancelling, the service checks the rate plan's cancellation policy:

```python
def calculate_refund(reservation: Reservation, cancelled_at: datetime) -> Decimal:
    policy = reservation.rate_plan.cancellation_policy
    days_before_checkin = (reservation.check_in - cancelled_at.date()).days

    if policy == CancellationPolicy.FREE:
        return reservation.total_amount
    elif policy == CancellationPolicy.NON_REFUNDABLE:
        return Decimal("0")
    elif policy == CancellationPolicy.H24 and days_before_checkin >= 1:
        return reservation.total_amount
    elif policy == CancellationPolicy.H48 and days_before_checkin >= 2:
        return reservation.total_amount
    elif policy == CancellationPolicy.H72 and days_before_checkin >= 3:
        return reservation.total_amount
    else:
        return Decimal("0")  # within cancellation window — no refund
```

## Kafka Events Published

```python
# On creation
await kafka_producer.send("reservation.created", {
    "event_type": "reservation.created",
    "tenant_id": str(tenant_id),
    "reservation_id": str(reservation.id),
    "channel": reservation.channel.value,
    "guest_email": guest.email,
    "check_in": reservation.check_in.isoformat(),
    "check_out": reservation.check_out.isoformat(),
    "room_type_id": str(reservation.room_type_id),
    "total_amount": float(reservation.total_amount),
    "currency": reservation.currency,
})

# On cancellation
await kafka_producer.send("reservation.cancelled", {
    "event_type": "reservation.cancelled",
    "tenant_id": str(tenant_id),
    "reservation_id": str(reservation.id),
    "channel": reservation.channel.value,
    "refund_amount": float(reservation.refund_amount or 0),
})
```
