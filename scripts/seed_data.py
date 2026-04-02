"""KIRA seed data script — populates development databases with sample data.

Run with:  uv run python scripts/seed_data.py
"""
import asyncio
import uuid

import asyncpg

POSTGRES_DSN = "postgresql://postgres:postgres@localhost:5432/kira"

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TENANT_SCHEMA = f"tenant_{str(TENANT_ID).replace('-', '_')}"


async def seed_tenant(conn: asyncpg.Connection) -> None:
    print(f"Creating tenant schema: {TENANT_SCHEMA}")
    await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{TENANT_SCHEMA}"')


async def seed_identity(conn: asyncpg.Connection) -> None:
    print("Seeding identity-service sample data...")
    # Insert a sample hotel property user into the public users table.
    # The identity-service manages this table; adapt column names as the
    # service schema evolves.
    await conn.execute(
        """
        INSERT INTO public.users (id, email, hashed_password, tenant_id, roles, is_active)
        VALUES ($1, $2, $3, $4, $5, TRUE)
        ON CONFLICT (email) DO NOTHING
        """,
        uuid.uuid4(),
        "demo@hotel-example.com",
        "$2b$12$placeholderHashReplaceWithRealBcryptHash",
        TENANT_ID,
        ["tenant_admin"],
    )


async def main() -> None:
    print("Connecting to PostgreSQL...")
    conn = await asyncpg.connect(POSTGRES_DSN)
    try:
        await seed_tenant(conn)
        await seed_identity(conn)
        print("Seed complete.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
