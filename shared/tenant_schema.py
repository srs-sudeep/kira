"""Load per-tenant DDL from shared/tenant_tables.sql (single source of truth)."""

from pathlib import Path


def get_tenant_tables_ddl() -> str:
    p = Path(__file__).resolve().parent / "tenant_tables.sql"
    return p.read_text(encoding="utf-8")
