# Database Schema — Multi-Tenant, Per-Service

## Strategy: Shared Cluster, Isolated Schemas

- One PostgreSQL 16 instance (RDS)
- `public` schema: global tables (tenants, users, audit_events, refresh_tokens)
- Per-tenant schemas (`tenant_{uuid_short}`): all business tables
- Each service owns specific tables but they all live in the tenant schema
- Middleware sets `SET search_path TO tenant_{id}, public` per request

### Table Ownership by Service

| Service | Tables Owned |
|---------|-------------|
| Identity | public.users, public.refresh_tokens, public.audit_events |
| Admin | public.tenants |
| Rate & Inventory | room_types, rate_plans, ari_snapshots, seasonal_rules, blackout_dates, inventory_history |
| Reservation | reservations, guest_profiles, reservation_notes |
| Channel Engine | channels, channel_mappings, sync_logs |
| Notification | notifications, notification_preferences |

### Migration Strategy

Each service has its own Alembic migration chain. When a new tenant is onboarded:
1. Admin Service creates the tenant record in `public.tenants`
2. Admin Service executes `CREATE SCHEMA tenant_{uuid}`
3. Admin Service runs each service's Alembic migrations against the new schema

For schema changes after initial setup:
1. Developer adds a migration in the relevant service's `migrations/versions/`
2. CI/CD runs the migration as a K8s Job before deploying the new service version
3. The migration runs against ALL tenant schemas (loop over public.tenants)

---

## Complete SQL Schema

### Public Schema (Global)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE public.tenants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    legal_name      VARCHAR(255),
    address_line1   VARCHAR(500),
    address_line2   VARCHAR(500),
    city            VARCHAR(100),
    state           VARCHAR(100),
    country         VARCHAR(3) DEFAULT 'IND',
    postal_code     VARCHAR(20),
    phone           VARCHAR(20),
    email           VARCHAR(255),
    website         VARCHAR(500),
    star_rating     SMALLINT CHECK (star_rating BETWEEN 1 AND 5),
    base_currency   VARCHAR(3) DEFAULT 'INR',
    timezone        VARCHAR(50) DEFAULT 'Asia/Kolkata',
    logo_url        VARCHAR(1000),
    subscription_tier VARCHAR(20) DEFAULT 'starter'
                    CHECK (subscription_tier IN ('free','starter','professional','enterprise')),
    schema_name     VARCHAR(100) UNIQUE NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    onboarded_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('super_admin','property_owner','revenue_manager','front_desk','read_only')),
    tenant_id       UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    is_active       BOOLEAN DEFAULT TRUE,
    mfa_enabled     BOOLEAN DEFAULT FALSE,
    mfa_secret      VARCHAR(500),
    last_login_at   TIMESTAMPTZ,
    failed_login_attempts INT DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_tenant ON public.users(tenant_id);

CREATE TABLE public.refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES public.tenants(id),
    user_id UUID REFERENCES public.users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    before_state JSONB,
    after_state JSONB,
    ip_address INET,
    user_agent VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
    -- NO updated_at — immutable
);
CREATE INDEX idx_audit_tenant_date ON public.audit_events(tenant_id, created_at DESC);
```

### Tenant Schema (Per-Property — all tables below exist once per tenant)

```sql
-- Owned by Rate & Inventory Service
CREATE TABLE room_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    max_occupancy INT NOT NULL DEFAULT 2,
    default_occupancy INT NOT NULL DEFAULT 2,
    bedding_type VARCHAR(20) CHECK (bedding_type IN ('single','double','twin','king','queen','mixed')),
    amenities JSONB DEFAULT '[]',
    images JSONB DEFAULT '[]',
    physical_inventory INT NOT NULL DEFAULT 0,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE rate_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_type_id UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    plan_type VARCHAR(20) NOT NULL CHECK (plan_type IN ('bar','non_refundable','corporate','package','promotional')),
    base_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    cancellation_policy JSONB,
    deposit_policy JSONB,
    derived_from_id UUID REFERENCES rate_plans(id),
    derived_type VARCHAR(10) CHECK (derived_type IN ('fixed','percentage')),
    derived_value DECIMAL(12,2),
    min_los INT DEFAULT 1,
    max_los INT DEFAULT 365,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ari_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_type_id UUID NOT NULL REFERENCES room_types(id),
    rate_plan_id UUID NOT NULL REFERENCES rate_plans(id),
    date DATE NOT NULL,
    available_rooms INT NOT NULL DEFAULT 0,
    rate_amount DECIMAL(12,2) NOT NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    cta_closed BOOLEAN DEFAULT FALSE,
    ctd_closed BOOLEAN DEFAULT FALSE,
    min_los INT DEFAULT 1,
    max_los INT DEFAULT 365,
    overbooking_buffer INT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_ari UNIQUE (room_type_id, rate_plan_id, date)
);
CREATE INDEX idx_ari_range ON ari_snapshots(room_type_id, date);

CREATE TABLE seasonal_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_type_id UUID REFERENCES room_types(id),
    rate_plan_id UUID REFERENCES rate_plans(id),
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    adjustment_type VARCHAR(10) NOT NULL CHECK (adjustment_type IN ('percentage','fixed')),
    adjustment_value DECIMAL(12,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE blackout_dates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL UNIQUE,
    reason VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE inventory_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_type_id UUID NOT NULL,
    rate_plan_id UUID NOT NULL,
    date DATE NOT NULL,
    field_changed VARCHAR(50) NOT NULL,
    old_value VARCHAR(100),
    new_value VARCHAR(100),
    changed_by UUID NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Owned by Reservation Service
CREATE TABLE guest_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email BYTEA,
    phone BYTEA,
    email_hash VARCHAR(64),
    nationality VARCHAR(3),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_guest_email ON guest_profiles(email_hash);

CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    confirmation_number VARCHAR(20) UNIQUE NOT NULL,
    channel_id UUID,
    source VARCHAR(20) NOT NULL CHECK (source IN ('booking_com','expedia','makemytrip','airbnb','agoda','direct','manual','phone')),
    room_type_id UUID NOT NULL,
    rate_plan_id UUID NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    nights INT GENERATED ALWAYS AS (check_out - check_in) STORED,
    guest_profile_id UUID NOT NULL REFERENCES guest_profiles(id),
    adults INT DEFAULT 1,
    children INT DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed' CHECK (status IN ('confirmed','modified','cancelled','no_show','checked_in','checked_out')),
    cancellation_policy JSONB,
    cancelled_at TIMESTAMPTZ,
    cancellation_reason VARCHAR(500),
    channel_reservation_id VARCHAR(100),
    special_requests TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_res_dates ON reservations(check_in, check_out);
CREATE INDEX idx_res_status ON reservations(status);
CREATE INDEX idx_res_source ON reservations(source);

CREATE TABLE reservation_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reservation_id UUID NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Owned by Channel Engine
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ota_code VARCHAR(30) NOT NULL CHECK (ota_code IN ('booking_com','expedia','makemytrip','airbnb','agoda','tripadvisor','hotelbeds')),
    display_name VARCHAR(255) NOT NULL,
    credentials_ref BYTEA NOT NULL,
    status VARCHAR(20) DEFAULT 'pending_certification' CHECK (status IN ('connected','disconnected','error','pending_certification')),
    last_sync_at TIMESTAMPTZ,
    error_message VARCHAR(1000),
    consecutive_failures INT DEFAULT 0,
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE channel_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    internal_room_type_id UUID NOT NULL,
    ota_room_type_id VARCHAR(100) NOT NULL,
    internal_rate_plan_id UUID NOT NULL,
    ota_rate_plan_id VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_mapping UNIQUE (channel_id, internal_room_type_id, internal_rate_plan_id)
);

CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID NOT NULL REFERENCES channels(id),
    event_type VARCHAR(20) NOT NULL CHECK (event_type IN ('ari_push','booking_pull','booking_push','error')),
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('outbound','inbound')),
    payload_hash VARCHAR(64),
    request_summary JSONB,
    response_status INT,
    response_summary JSONB,
    retry_count INT DEFAULT 0,
    status VARCHAR(10) NOT NULL CHECK (status IN ('success','failed','retrying')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_sync_channel ON sync_logs(channel_id, created_at DESC);

-- Owned by Notification Service
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    type VARCHAR(30) NOT NULL CHECK (type IN ('new_booking','cancellation','channel_failure','low_inventory','rate_parity','system')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_notif_user ON notifications(user_id, is_read, created_at DESC);

CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    email_enabled BOOLEAN DEFAULT TRUE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_pref UNIQUE (user_id, event_type)
);
```
