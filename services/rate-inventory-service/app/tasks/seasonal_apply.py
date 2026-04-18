"""Celery beat task: nightly application of seasonal pricing rules.

Runs at 01:00 UTC every night. Iterates all active tenants, sets search_path
per tenant, then delegates to ARIService.apply_seasonal_rules().
"""

import asyncio
import uuid

import structlog
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.services.ari_service import ARIService
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)

# System user ID used as changed_by for automated rule applications
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _apply_for_tenant(tenant_id: uuid.UUID, schema_name: str) -> int:
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
            svc = ARIService(session, tenant_id=tenant_id)
            count = await svc.apply_seasonal_rules(
                tenant_id=tenant_id,
                changed_by=SYSTEM_USER_ID,
            )
            await session.commit()
            return count
        except Exception as exc:
            await session.rollback()
            logger.error(
                "seasonal_apply_failed_for_tenant",
                tenant_id=str(tenant_id),
                exc=str(exc),
            )
            return 0


async def _run_all() -> dict[str, int]:
    """Fetch all active tenants and apply seasonal rules to each."""
    summary: dict[str, int] = {}
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id, schema_name FROM public.tenants WHERE is_active = true"))
        tenants = result.fetchall()

    for row in tenants:
        tenant_id = uuid.UUID(str(row[0]))
        schema_name: str = row[1]
        count = await _apply_for_tenant(tenant_id, schema_name)
        summary[str(tenant_id)] = count
        logger.info(
            "seasonal_rules_applied",
            tenant_id=str(tenant_id),
            cells_updated=count,
        )
    return summary


@celery_app.task(name="app.tasks.seasonal_apply.apply_seasonal_rules_all_tenants", bind=True)
def apply_seasonal_rules_all_tenants(self) -> dict:
    """Synchronous Celery entry point — runs the async logic in an event loop."""
    try:
        result = asyncio.run(_run_all())
        total = sum(result.values())
        logger.info("nightly_seasonal_apply_complete", tenants=len(result), total_cells=total)
        return {"tenants_processed": len(result), "total_cells_updated": total}
    except Exception as exc:
        logger.error("nightly_seasonal_apply_error", exc=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=2)
