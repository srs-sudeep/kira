"""KIRA super-admin creation script — creates a platform-level super_admin user.

Run with:  uv run python scripts/create_superadmin.py
Prompts for email and password interactively.
"""
import asyncio
import getpass
import os
import uuid

import asyncpg
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

POSTGRES_DSN = os.environ.get(
    "POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/kira"
)

pwd_hash = PasswordHash([BcryptHasher()])


async def create_superadmin(email: str, password: str) -> None:
    conn = await asyncpg.connect(POSTGRES_DSN)
    try:
        hashed = pwd_hash.hash(password)
        user_id = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO public.users
                (id, email, hashed_password, tenant_id, roles, is_active, is_superadmin)
            VALUES ($1, $2, $3, NULL, $4, TRUE, TRUE)
            ON CONFLICT (email) DO UPDATE
                SET hashed_password = EXCLUDED.hashed_password,
                    roles = EXCLUDED.roles,
                    is_superadmin = TRUE
            """,
            user_id,
            email,
            hashed,
            ["super_admin"],
        )
        print(f"Super-admin created/updated: {email} (id={user_id})")
    finally:
        await conn.close()


def main() -> None:
    print("=== KIRA Super-Admin Setup ===")
    email = input("Email: ").strip()
    if not email:
        raise SystemExit("Email cannot be empty.")
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match.")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")

    asyncio.run(create_superadmin(email, password))


if __name__ == "__main__":
    main()
