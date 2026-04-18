"""KIRA seed data script — populates development databases with sample data.

Run on the host (Postgres on localhost:5432):
  uv run python scripts/seed_data.py

Run against Docker Compose Postgres from the host (same DSN if port 5432 is published):
  POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/kira uv run python scripts/seed_data.py

From another machine / CI targeting the DB container by hostname:
  POSTGRES_DSN=postgresql://postgres:postgres@postgres:5432/kira python scripts/seed_data.py

Dependencies: ``asyncpg`` is declared on the repo-root ``kira-cli`` package so
``uv run python scripts/seed_data.py`` works from the monorepo root. The Docker
``seed-data`` service also installs ``cryptography`` if ever needed by this script.

Also set ``ENCRYPTION_KEY`` to the same 64-char hex as reservation-service and channel-engine
(see ``.env.local``) so guest PII and channel credentials match running services.

Run order: **migrations first** (``make migrate-docker-all`` or ``make bootstrap``), then this seed.

Dev logins (domains must pass API ``EmailStr`` — do not use ``*.local``):

- **Super admin:** ``admin@example.com`` / ``Admin1234!``
- **Hotel admin:** ``manager@grandhotel.example.com`` / ``Manager1234!``
- **Revenue / front desk:** ``revenue@grandhotel.example.com`` / ``Manager1234!`` · ``frontdesk@grandhotel.example.com`` / ``Manager1234!``

Re-run this script to refresh passwords, tenant DDL, and demo business data (tenant tables are truncated then re-seeded).
"""
import asyncio
import os
import sys
import uuid
from pathlib import Path

import asyncpg

_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# bcrypt cost 12; verified by identity-service ``pwdlib`` (passwords above)
_HASH_ADMIN = "$2b$12$6On7FtKxl/UCcSvKEwJ9fOQs7dNNHwms8NW2wI9w42jMpEs.tNSsO"  # Admin1234!
_HASH_MANAGER = "$2b$12$Xzp6m0YfspI3wlJXK3R5Jufb0nHgqtWa3VMyP9Qva369tajVcByzm"  # Manager1234!

POSTGRES_DSN = os.environ.get(
    "POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/kira"
)

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TENANT_SCHEMA = f"tenant_{str(TENANT_ID).replace('-', '_')}"

# Stable user IDs (so tenant notifications and notes reference valid users)
DEV_ADMIN_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
DEV_MANAGER_ID = uuid.UUID("10000000-0000-0000-0000-000000000002")
DEV_REVENUE_ID = uuid.UUID("10000000-0000-0000-0000-000000000003")
DEV_FRONT_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")

# ── Default permissions: (resource, action, description) ──────────────────────
DEFAULT_PERMISSIONS: list[tuple[str, str, str]] = [
    # Dashboard
    ("dashboard", "read", "View dashboard KPIs and charts"),
    # Users
    ("users", "create", "Invite new users"),
    ("users", "read", "View user list and profiles"),
    ("users", "update", "Edit user details and roles"),
    ("users", "delete", "Deactivate users"),
    # Rooms
    ("rooms", "create", "Create room types"),
    ("rooms", "read", "View room types"),
    ("rooms", "update", "Edit room types"),
    ("rooms", "delete", "Delete room types"),
    # Rates
    ("rates", "create", "Create rate plans"),
    ("rates", "read", "View rate plans"),
    ("rates", "update", "Edit rate plans"),
    ("rates", "delete", "Delete rate plans"),
    # Inventory (ARI calendar)
    ("inventory", "read", "View ARI calendar"),
    ("inventory", "update", "Bulk update availability, rates, and restrictions"),
    # Reservations
    ("reservations", "create", "Create manual reservations"),
    ("reservations", "read", "View reservations"),
    ("reservations", "update", "Modify reservations"),
    ("reservations", "cancel", "Cancel reservations"),
    # Channels
    ("channels", "create", "Connect OTA channels"),
    ("channels", "read", "View channel connections and sync log"),
    ("channels", "update", "Edit channel mappings and settings"),
    ("channels", "delete", "Disconnect channels"),
    ("channels", "sync", "Trigger manual ARI sync"),
    # Notifications
    ("notifications", "read", "View notifications"),
    ("notifications", "update", "Mark notifications as read and configure preferences"),
    # Settings
    ("settings", "read", "View property settings"),
    ("settings", "update", "Edit property settings"),
    # Audit
    ("audit", "read", "View audit log"),
    # Admin (super_admin only by default)
    ("tenants", "create", "Create new tenants"),
    ("tenants", "read", "View tenant list"),
    ("tenants", "update", "Edit tenant settings"),
    ("tenants", "delete", "Deactivate tenants"),
    ("permissions", "manage", "Manage permissions and role assignments"),
]

# ── Role → permission codes ──────────────────────────────────────────────────
# super_admin gets everything automatically via the require_permission dependency
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "property_owner": [
        "dashboard:read",
        "users:create", "users:read", "users:update", "users:delete",
        "rooms:create", "rooms:read", "rooms:update", "rooms:delete",
        "rates:create", "rates:read", "rates:update", "rates:delete",
        "inventory:read", "inventory:update",
        "reservations:create", "reservations:read", "reservations:update", "reservations:cancel",
        "channels:create", "channels:read", "channels:update", "channels:delete", "channels:sync",
        "notifications:read", "notifications:update",
        "settings:read", "settings:update",
        "audit:read",
    ],
    "revenue_manager": [
        "dashboard:read",
        "rooms:read", "rooms:update",
        "rates:create", "rates:read", "rates:update", "rates:delete",
        "inventory:read", "inventory:update",
        "reservations:read",
        "channels:read", "channels:update", "channels:sync",
        "notifications:read", "notifications:update",
        "audit:read",
    ],
    "front_desk": [
        "dashboard:read",
        "rooms:read",
        "rates:read",
        "inventory:read",
        "reservations:create", "reservations:read", "reservations:update",
        "notifications:read", "notifications:update",
    ],
    "read_only": [
        "dashboard:read",
        "rooms:read",
        "rates:read",
        "inventory:read",
        "reservations:read",
        "channels:read",
        "notifications:read",
    ],
}


async def seed_tenant(conn: asyncpg.Connection) -> None:
    print(f"Creating tenant schema: {TENANT_SCHEMA}")
    await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{TENANT_SCHEMA}"')


async def ensure_tenants_table(conn: asyncpg.Connection) -> None:
    row = await conn.fetchrow(
        """
        SELECT 1 AS ok
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'tenants'
        """
    )
    if not row:
        raise RuntimeError(
            'Table "public.tenants" does not exist. Run migrations first (admin-service must run '
            "before seeding):\n"
            "  make migrate-docker-all\n"
            "or:  make bootstrap"
        )


async def ensure_demo_tenant_row(conn: asyncpg.Connection) -> None:
    """Insert the dev tenant row so users.tenant_id FK succeeds."""
    await conn.execute(
        """
        INSERT INTO public.tenants (id, name, schema_name)
        VALUES ($1, 'Grand Hotel Demo', $2)
        ON CONFLICT (id) DO NOTHING
        """,
        TENANT_ID,
        TENANT_SCHEMA,
    )
    await conn.execute(
        """
        UPDATE public.tenants SET
            city = 'New York',
            country = 'USA',
            timezone = 'America/New_York',
            base_currency = 'USD'
        WHERE id = $1
        """,
        TENANT_ID,
    )


async def ensure_identity_tables(conn: asyncpg.Connection) -> None:
    row = await conn.fetchrow(
        """
        SELECT 1 AS ok
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'users'
        """
    )
    if not row:
        raise RuntimeError(
            'Table "public.users" does not exist. Run Alembic migrations before seeding:\n'
            "  make migrate-docker-all\n"
            "or one-shot first-time setup:\n"
            "  make bootstrap"
        )


async def seed_identity(conn: asyncpg.Connection) -> None:
    await ensure_identity_tables(conn)
    print(
        "Seeding identity users (admin, manager, revenue, front desk) with stable UUIDs..."
    )
    await conn.execute(
        """
        INSERT INTO public.users (
            id, email, hashed_password, first_name, last_name, role, tenant_id, is_active
        )
        VALUES
            ($1, 'admin@example.com', $2, 'Platform', 'Admin', 'super_admin', NULL, TRUE),
            ($3, 'manager@grandhotel.example.com', $4, 'Grand Hotel', 'Manager', 'property_owner', $5, TRUE),
            ($6, 'revenue@grandhotel.example.com', $7, 'Riley', 'Revenue', 'revenue_manager', $5, TRUE),
            ($8, 'frontdesk@grandhotel.example.com', $7, 'Frank', 'Desk', 'front_desk', $5, TRUE)
        ON CONFLICT (email) DO UPDATE SET
            hashed_password = EXCLUDED.hashed_password,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            role = EXCLUDED.role,
            tenant_id = EXCLUDED.tenant_id,
            is_active = EXCLUDED.is_active,
            updated_at = now()
        """,
        DEV_ADMIN_ID,
        _HASH_ADMIN,
        DEV_MANAGER_ID,
        _HASH_MANAGER,
        TENANT_ID,
        DEV_REVENUE_ID,
        _HASH_MANAGER,
        DEV_FRONT_ID,
    )


async def seed_permissions(conn: asyncpg.Connection) -> None:
    print("Seeding permissions...")

    # Ensure tables exist (skip if migrations haven't run yet)
    has_table = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = 'permissions')"
    )
    if not has_table:
        print("  permissions table not found — skipping (run migrations first)")
        return

    perm_ids: dict[str, uuid.UUID] = {}

    for resource, action, description in DEFAULT_PERMISSIONS:
        code = f"{resource}:{action}"
        row = await conn.fetchrow(
            "SELECT id FROM public.permissions WHERE resource = $1 AND action = $2",
            resource,
            action,
        )
        if row:
            perm_ids[code] = row["id"]
        else:
            perm_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO public.permissions (id, resource, action, description)
                VALUES ($1, $2, $3, $4)
                """,
                perm_id,
                resource,
                action,
                description,
            )
            perm_ids[code] = perm_id
            print(f"  + {code}")

    print("Seeding role-permission mappings...")
    for role, codes in ROLE_PERMISSIONS.items():
        for code in codes:
            if code not in perm_ids:
                continue
            await conn.execute(
                """
                INSERT INTO public.role_permissions (id, role, permission_id)
                VALUES ($1, $2, $3)
                ON CONFLICT ON CONSTRAINT uq_role_permission DO NOTHING
                """,
                uuid.uuid4(),
                role,
                perm_ids[code],
            )
        print(f"  {role}: {len(codes)} permissions")


async def get_user_id_by_email(conn: asyncpg.Connection, email: str) -> uuid.UUID | None:
    """Return current PK for a user (may differ from DEV_* constants after ON CONFLICT upsert)."""
    row = await conn.fetchrow("SELECT id FROM public.users WHERE email = $1", email)
    return row["id"] if row else None


async def seed_audit_sample(conn: asyncpg.Connection, manager_user_id: uuid.UUID) -> None:
    has = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = 'audit_events')"
    )
    if not has:
        return
    print("Seeding audit_events sample rows...")
    for i in range(12):
        await conn.execute(
            """
            INSERT INTO public.audit_events (
                id, tenant_id, user_id, action, resource_type, resource_id, metadata, created_at
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7::jsonb,
                NOW() - ($8::integer * interval '1 day')
            )
            """,
            uuid.uuid4(),
            TENANT_ID,
            manager_user_id,
            "login" if i % 2 == 0 else "update",
            "user" if i % 2 == 0 else "reservation",
            f"res-{i}" if i % 2 else None,
            '{"source":"seed"}',
            i % 14,
        )


async def main() -> None:
    print("Connecting to PostgreSQL...")
    conn = await asyncpg.connect(POSTGRES_DSN)
    try:
        await ensure_tenants_table(conn)
        await seed_tenant(conn)
        await ensure_demo_tenant_row(conn)
        await seed_identity(conn)
        await seed_permissions(conn)

        manager_id = await get_user_id_by_email(conn, "manager@grandhotel.example.com")
        if manager_id is None:
            raise RuntimeError(
                "Expected manager@grandhotel.example.com after seed_identity — check users table."
            )

        await seed_audit_sample(conn, manager_id)

        ddl_path = _REPO_ROOT / "shared" / "tenant_tables.sql"
        if not ddl_path.is_file():
            raise FileNotFoundError(f"Missing {ddl_path}")
        ddl_sql = ddl_path.read_text(encoding="utf-8")

        from seed_tenant_business import (
            apply_tenant_ddl,
            seed_tenant_business_data,
            truncate_tenant_data,
        )

        print(f"Applying tenant DDL + demo data in {TENANT_SCHEMA}...")
        await apply_tenant_ddl(conn, TENANT_SCHEMA, ddl_sql)
        await truncate_tenant_data(conn, TENANT_SCHEMA)
        await seed_tenant_business_data(
            conn,
            tenant_schema=TENANT_SCHEMA,
            manager_user_id=manager_id,
        )
        print("Seed complete.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
