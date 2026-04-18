"""initial — create public.tenants table

Revision ID: 0001
Revises:
Create Date: 2026-04-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=True),
        sa.Column("address_line1", sa.String(500), nullable=True),
        sa.Column("address_line2", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("country", sa.String(3), nullable=False, server_default="IND"),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("star_rating", sa.SmallInteger(), nullable=True),
        sa.Column("base_currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("logo_url", sa.String(1000), nullable=True),
        sa.Column(
            "subscription_tier",
            sa.String(20),
            nullable=False,
            server_default="starter",
        ),
        sa.Column("schema_name", sa.String(100), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("onboarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "star_rating BETWEEN 1 AND 5",
            name="ck_tenant_star_rating",
        ),
        sa.CheckConstraint(
            "subscription_tier IN ('free','starter','professional','enterprise')",
            name="ck_tenant_subscription_tier",
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("tenants", schema="public")
