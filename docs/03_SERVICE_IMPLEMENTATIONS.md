# Service Implementations — Per-Service Prompts

Each section below is a self-contained prompt for building one microservice. Feed the prompt along with the service template from `02_MONOREPO_STRUCTURE.md`.

**Build order:** Identity → Admin → Rate & Inventory → Reservation → Channel Engine → Notification

---

## Service 1: Identity Service (Sprint 1)

**Location:** `services/identity-service/`
**Port:** 8001
**Owns:** users, refresh_tokens, audit_events tables

### Models
- `User`: id (UUID PK), email (unique), hashed_password, first_name, last_name, role (enum: super_admin, property_owner, revenue_manager, front_desk, read_only), tenant_id (FK→tenants, nullable for super_admin), is_active, mfa_enabled, mfa_secret (encrypted), last_login_at, failed_login_attempts, locked_until, created_at, updated_at
- `RefreshToken`: id (UUID), user_id (FK), token_hash, expires_at, revoked, created_at
- `AuditEvent`: id (UUID), tenant_id, user_id, action, resource_type, resource_id, before_state (JSONB), after_state (JSONB), ip_address, user_agent, metadata (JSONB), created_at — IMMUTABLE, no updated_at

### API Endpoints
- `POST /auth/register` — Create user (requires admin). Sends invitation email via Celery.
- `POST /auth/login` — Authenticate. Returns access_token + refresh_token. If MFA enabled, returns mfa_required: true + temp_token.
- `POST /auth/login/mfa` — Verify TOTP code with temp_token.
- `POST /auth/refresh` — Rotate refresh token.
- `POST /auth/logout` — Revoke refresh token.
- `POST /auth/mfa/setup` — Generate TOTP secret + provisioning URI.
- `POST /auth/mfa/enable` — Verify code, enable MFA.
- `GET /auth/me` — Current user profile.
- `PATCH /auth/me` — Update profile (name, password).
- `GET /users` — List users for tenant (paginated). Requires admin.
- `POST /users/invite` — Invite user via email.
- `PATCH /users/{id}` — Update role, active status.
- `DELETE /users/{id}` — Soft delete.
- `GET /audit` — List audit events (paginated, filterable). Requires admin.
- `GET /health` — Service health check.
- `POST /internal/validate-token` — Internal endpoint (no gateway) — other services call this to validate JWT.

### Business Logic
- Brute-force protection: 5 failed attempts → lock for 15 min.
- JWT access tokens: 30min expiry. Refresh tokens: 7 days, rotated on use.
- MFA via pyotp (TOTP). Secret encrypted at rest.
- Every login, logout, failed login, role change → AuditEvent record.
- Password hashing: bcrypt via passlib.

---

## Service 2: Admin / Tenant Service (Sprint 1)

**Location:** `services/admin-service/`
**Port:** 8006
**Owns:** tenants, tenant_configs tables

### Models
- `Tenant`: id (UUID PK), name, legal_name, address (line1, line2, city, state, country, postal_code), phone, email, website, star_rating (1-5), base_currency (default INR), timezone (default Asia/Kolkata), logo_url, subscription_tier (free/starter/professional/enterprise), schema_name (unique, e.g. tenant_a1b2c3d4), is_active, onboarded_at, created_at, updated_at

### API Endpoints
- `POST /tenants` — Create tenant (super_admin). Creates record + provisions new PostgreSQL schema.
- `GET /tenants` — List all tenants (super_admin, paginated).
- `GET /tenants/me` — Current tenant details.
- `PATCH /tenants/me` — Update tenant config (property_owner).
- `GET /tenants/{id}` — Get specific tenant (super_admin).
- `PATCH /tenants/{id}` — Update subscription tier, active status (super_admin).

### Business Logic
- `create_tenant()`: Insert tenant record in public schema → execute `CREATE SCHEMA tenant_{short_uuid}` → run Alembic migrations for all services' tables within the new schema.
- This service coordinates schema creation. Each other service's tables are created in the tenant schema.

---

## Service 3: Rate & Inventory Service (Sprint 2)

**Location:** `services/rate-inventory-service/`
**Port:** 8002
**Owns:** room_types, rate_plans, ari_snapshots, seasonal_rules, blackout_dates, inventory_history

### Models
- `RoomType`: id, name, description, max_occupancy, bedding_type, amenities (JSONB), images (JSONB), physical_inventory, is_active
- `RatePlan`: id, room_type_id (FK), name, plan_type (bar/non_refundable/corporate/package), base_amount, currency, cancellation_policy (JSONB), derived_from_id (FK self), derived_type, derived_value, min_los, max_los, is_active
- `ARISnapshot`: room_type_id + rate_plan_id + date (unique composite), available_rooms, rate_amount, is_closed, cta_closed, ctd_closed, min_los, max_los
- `SeasonalRule`: room_type_id, rate_plan_id (nullable), start_date, end_date, adjustment_type, adjustment_value
- `BlackoutDate`: date (unique), reason
- `InventoryHistory`: room_type_id, rate_plan_id, date, field_changed, old_value, new_value, changed_by, changed_at

### API Endpoints
- CRUD `/rooms/types` and `/rooms/types/{id}/rate-plans`
- `GET /inventory/calendar?room_type_id=&start_date=&end_date=` — ARI grid data
- `PUT /inventory/calendar` — Update ARI cells
- `POST /inventory/bulk-update` — Bulk update across room types/dates
- `POST /inventory/stop-sell` — Apply stop-sell
- CRUD `/inventory/seasonal-rules` and `/inventory/blackout-dates`
- `GET /inventory/history`

### Kafka Events Published
- `ari.updated` — Every time ARI changes (calendar edit, bulk update, stop-sell, seasonal rule application). Payload: tenant_id, room_type_id, rate_plan_id, date_range, changed_fields.

### Business Logic
- Derived rates: when parent rate changes, recalculate all children (percentage or fixed offset).
- Seasonal rules: Celery beat task runs nightly, applies rules to upcoming 365 days.
- Blackout dates: set is_closed=true on all ARISnapshots for that date.
- All changes logged to InventoryHistory with before/after values.

---

## Service 4: Reservation Service (Sprint 2)

**Location:** `services/reservation-service/`
**Port:** 8003
**Owns:** reservations, guest_profiles, reservation_notes

### Models
- `Reservation`: id, confirmation_number (auto: AAB-XXXXXX), channel_id, source (enum), room_type_id, rate_plan_id, check_in, check_out, nights (computed), guest_profile_id (FK), adults, children, total_amount, currency, status (confirmed/modified/cancelled/no_show/checked_in/checked_out), cancelled_at, cancellation_reason, channel_reservation_id
- `GuestProfile`: id, first_name, last_name, email (encrypted BYTEA), phone (encrypted), email_hash (SHA-256 for lookup), nationality, preferences (JSONB)
- `ReservationNote`: id, reservation_id (FK), user_id, content, created_at

### API Endpoints
- `GET /reservations` — Unified inbox (paginated, filterable by status/source/dates/guest)
- `GET /reservations/{id}` — Full detail with guest + notes
- `POST /reservations` — Manual booking (walk-in/phone)
- `PATCH /reservations/{id}` — Modify (dates, room, guest count)
- `POST /reservations/{id}/cancel` — Cancel with policy application
- `POST /reservations/{id}/notes` — Add internal note
- `GET /reservations/duplicates` — Flagged potential duplicates

### Kafka Events
- Publishes: `reservation.created`, `reservation.modified`, `reservation.cancelled`
- Consumes: channel engine publishes raw booking data → reservation service creates the record

### Business Logic
- Manual booking: validate availability (call Rate Service via REST), decrement ARI, create reservation.
- Channel booking: consumed from Kafka, create/match guest profile, create reservation, decrement ARI.
- Duplicate detection: same email_hash + overlapping dates + same room type.
- Guest PII encrypted with AES-256. email_hash for lookups without decryption.

---

## Service 5: Channel Engine (Sprint 3)

**Location:** `services/channel-engine/`
**Port:** 8004
**Owns:** channels, channel_mappings, sync_logs

### Adapter Pattern
```python
# app/adapters/base.py
class ChannelAdapter(ABC):
    async def test_connection(self, credentials: dict) -> bool: ...
    async def push_ari(self, updates: list[ARIUpdate]) -> dict: ...
    async def pull_bookings(self, since: str) -> list[BookingData]: ...
```
Each OTA: `booking_com.py`, `expedia.py`, `makemytrip.py` implements this interface.

### API Endpoints
- `POST /channels` — Connect channel (validates credentials via test API call)
- `GET /channels` — List with health status
- `PATCH /channels/{id}` — Update config/credentials
- `DELETE /channels/{id}` — Disconnect
- CRUD `/channels/{id}/mapping` — Room/rate mappings
- `GET /channels/health` — Dashboard health summary
- `GET /channels/{id}/sync-log` — Sync event log
- `POST /channels/{id}/sync` — Manual full resync trigger

### Kafka Events
- Consumes: `ari.updated` → resolves mappings → pushes to OTAs
- Publishes: `channel.sync.result` (success/failure), raw booking data for reservation service

### Background Tasks (Celery)
- `ari_push`: triggered by Kafka consumer, pushes ARI to all mapped channels
- `booking_pull`: Celery beat every 60s per active channel, polls for new bookings
- Retry: exponential back-off 1s → 4s → 16s, max 3 retries
- Circuit breaker: 5 consecutive failures → channel.status = error, stop pushing until manual reconnect or 5-min auto-recovery

---

## Service 6: Notification Service (Sprint 3)

**Location:** `services/notification-service/`
**Port:** 8005
**Owns:** notifications, notification_preferences

### API Endpoints
- `GET /notifications` — List for current user (paginated, filterable by type/read status)
- `GET /notifications/unread-count` — Count of unread
- `PATCH /notifications/{id}/read` — Mark as read
- `POST /notifications/mark-all-read` — Bulk mark read
- `GET /notifications/preferences` — User preferences
- `PATCH /notifications/preferences` — Update preferences

### Kafka Events Consumed
- `reservation.created` → notify front desk + property owner (in-app + email)
- `reservation.cancelled` → notify front desk + property owner
- `channel.sync.failed` → notify property owner + revenue manager

### Business Logic
- Create notifications in bulk (one per recipient user in the tenant).
- Email sending via Celery task (never block the API response).
- Respect user preferences: check if email/in-app enabled for the event type before creating.
