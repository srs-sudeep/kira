-- Per-tenant schema DDL — single source for admin provisioning and dev seed.
-- Rate & Inventory Service

CREATE TABLE IF NOT EXISTS room_types (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    max_occupancy       INT NOT NULL DEFAULT 2,
    default_occupancy   INT NOT NULL DEFAULT 2,
    bedding_type        VARCHAR(20) CHECK (bedding_type IN ('single','double','twin','king','queen','mixed')),
    amenities           JSONB DEFAULT '[]',
    images              JSONB DEFAULT '[]',
    physical_inventory  INT NOT NULL DEFAULT 0,
    sort_order          INT DEFAULT 0,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rate_plans (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_type_id        UUID NOT NULL REFERENCES room_types(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    plan_type           VARCHAR(20) NOT NULL CHECK (plan_type IN ('bar','non_refundable','corporate','package','promotional')),
    base_amount         DECIMAL(12,2) NOT NULL,
    currency            VARCHAR(3) DEFAULT 'INR',
    cancellation_policy JSONB,
    deposit_policy      JSONB,
    derived_from_id     UUID REFERENCES rate_plans(id),
    derived_type        VARCHAR(10) CHECK (derived_type IN ('fixed','percentage')),
    derived_value       DECIMAL(12,2),
    min_los             INT DEFAULT 1,
    max_los             INT DEFAULT 365,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ari_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_type_id    UUID NOT NULL REFERENCES room_types(id),
    rate_plan_id    UUID NOT NULL REFERENCES rate_plans(id),
    date            DATE NOT NULL,
    available_rooms INT NOT NULL DEFAULT 0,
    rate_amount     DECIMAL(12,2) NOT NULL,
    is_closed       BOOLEAN DEFAULT FALSE,
    cta_closed      BOOLEAN DEFAULT FALSE,
    ctd_closed      BOOLEAN DEFAULT FALSE,
    min_los         INT DEFAULT 1,
    max_los         INT DEFAULT 365,
    overbooking_buffer INT DEFAULT 0,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_ari UNIQUE (room_type_id, rate_plan_id, date)
);
CREATE INDEX IF NOT EXISTS idx_ari_range ON ari_snapshots(room_type_id, date);

CREATE TABLE IF NOT EXISTS seasonal_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_type_id    UUID REFERENCES room_types(id),
    rate_plan_id    UUID REFERENCES rate_plans(id),
    name            VARCHAR(255) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    adjustment_type VARCHAR(10) NOT NULL CHECK (adjustment_type IN ('percentage','fixed')),
    adjustment_value DECIMAL(12,2) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS blackout_dates (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date        DATE NOT NULL UNIQUE,
    reason      VARCHAR(500),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_type_id    UUID NOT NULL,
    rate_plan_id    UUID NOT NULL,
    date            DATE NOT NULL,
    field_changed   VARCHAR(50) NOT NULL,
    old_value       VARCHAR(100),
    new_value       VARCHAR(100),
    changed_by      UUID NOT NULL,
    changed_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Reservation Service

CREATE TABLE IF NOT EXISTS guest_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    email       BYTEA,
    phone       BYTEA,
    email_hash  VARCHAR(64),
    nationality VARCHAR(3),
    preferences JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_guest_email ON guest_profiles(email_hash);

CREATE TABLE IF NOT EXISTS reservations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    confirmation_number     VARCHAR(20) UNIQUE NOT NULL,
    channel_id              UUID,
    source                  VARCHAR(20) NOT NULL CHECK (source IN ('booking_com','expedia','makemytrip','airbnb','agoda','direct','manual','phone')),
    room_type_id            UUID NOT NULL,
    rate_plan_id            UUID NOT NULL,
    check_in                DATE NOT NULL,
    check_out               DATE NOT NULL,
    nights                  INT GENERATED ALWAYS AS (check_out - check_in) STORED,
    guest_profile_id        UUID NOT NULL REFERENCES guest_profiles(id),
    adults                  INT DEFAULT 1,
    children                INT DEFAULT 0,
    total_amount            DECIMAL(12,2) NOT NULL,
    currency                VARCHAR(3) DEFAULT 'INR',
    status                  VARCHAR(20) NOT NULL DEFAULT 'confirmed' CHECK (status IN ('confirmed','modified','cancelled','no_show','checked_in','checked_out')),
    cancellation_policy     JSONB,
    cancelled_at            TIMESTAMPTZ,
    cancellation_reason     VARCHAR(500),
    channel_reservation_id  VARCHAR(100),
    special_requests        TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_res_dates  ON reservations(check_in, check_out);
CREATE INDEX IF NOT EXISTS idx_res_status ON reservations(status);
CREATE INDEX IF NOT EXISTS idx_res_source ON reservations(source);

CREATE TABLE IF NOT EXISTS reservation_notes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reservation_id  UUID NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL,
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Channel Engine

CREATE TABLE IF NOT EXISTS channels (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ota_code                VARCHAR(30) NOT NULL CHECK (ota_code IN ('booking_com','expedia','makemytrip','airbnb','agoda','tripadvisor','hotelbeds')),
    display_name            VARCHAR(255) NOT NULL,
    credentials_ref         BYTEA NOT NULL,
    status                  VARCHAR(20) DEFAULT 'pending_certification' CHECK (status IN ('connected','disconnected','error','pending_certification')),
    last_sync_at            TIMESTAMPTZ,
    error_message           VARCHAR(1000),
    consecutive_failures    INT DEFAULT 0,
    config                  JSONB DEFAULT '{}',
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS channel_mappings (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id              UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    internal_room_type_id   UUID NOT NULL,
    ota_room_type_id        VARCHAR(100) NOT NULL,
    internal_rate_plan_id   UUID NOT NULL,
    ota_rate_plan_id        VARCHAR(100) NOT NULL,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_mapping UNIQUE (channel_id, internal_room_type_id, internal_rate_plan_id)
);

CREATE TABLE IF NOT EXISTS sync_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id      UUID NOT NULL REFERENCES channels(id),
    event_type      VARCHAR(20) NOT NULL CHECK (event_type IN ('ari_push','booking_pull','booking_push','error')),
    direction       VARCHAR(10) NOT NULL CHECK (direction IN ('outbound','inbound')),
    payload_hash    VARCHAR(64),
    request_summary JSONB,
    response_status INT,
    response_summary JSONB,
    retry_count     INT DEFAULT 0,
    status          VARCHAR(10) NOT NULL CHECK (status IN ('success','failed','retrying')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sync_channel ON sync_logs(channel_id, created_at DESC);

-- Notification Service

CREATE TABLE IF NOT EXISTS notifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID,
    type        VARCHAR(30) NOT NULL CHECK (type IN ('new_booking','cancellation','channel_failure','low_inventory','rate_parity','system')),
    title       VARCHAR(255) NOT NULL,
    message     TEXT NOT NULL,
    data        JSONB DEFAULT '{}',
    is_read     BOOLEAN DEFAULT FALSE,
    read_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notif_user_read_ts ON notifications(user_id, is_read, created_at DESC);

CREATE TABLE IF NOT EXISTS notification_preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    event_type      VARCHAR(30) NOT NULL,
    email_enabled   BOOLEAN DEFAULT TRUE,
    in_app_enabled  BOOLEAN DEFAULT TRUE,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_pref UNIQUE (user_id, event_type)
);
