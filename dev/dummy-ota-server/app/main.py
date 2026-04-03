"""Minimal HTTP stand-in for OTA partner APIs — local Docker dev only."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.seed_data import HOTELS, RESERVATIONS, ROOM_TYPES, RATE_PLANS, inventory_snapshot

app = FastAPI(
    title="KIRA Dummy OTA Partner API",
    version="0.1.0",
    description=(
        "Fake OTA-style REST API for local development. "
        "Not wired into channel-engine adapters by default (those are stubs). "
        "\n\n**Test credentials** (any other values get 401):\n"
        "- **booking_com**: `hotel_id`=`DUMMY-BDC-001`, `api_key`=`dummy-bdc-key`\n"
        "- **expedia**: `hotel_id`=`DUMMY-EXP-001`, `client_id`=`dummy-exp-client`, "
        "`api_secret`=`dummy-exp-secret`\n"
        "- **makemytrip**: `property_id`=`DUMMY-MMT-001`, `access_key`=`dummy-mmt-access`, "
        "`secret_key`=`dummy-mmt-secret`\n"
    ),
)


# ── In-memory log of ARI pushes (for debugging) ─────────────────────────────
_ari_push_log: list[dict[str, Any]] = []


def _hotel_or_404(hotel_id: str) -> dict[str, Any]:
    for h in HOTELS:
        if h["hotel_id"] == hotel_id:
            return h
    raise HTTPException(status_code=404, detail=f"Unknown hotel_id: {hotel_id}")


def _parse_since(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # Accept date or datetime
        if len(s) == 10:
            dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid since (use ISO-8601 date or datetime)") from None


class AuthVerifyRequest(BaseModel):
    ota: Literal["booking_com", "expedia", "makemytrip"]
    credentials: dict[str, Any]


class InventoryCell(BaseModel):
    ota_room_type_id: str
    ota_rate_plan_id: str
    date: str
    available_rooms: int = Field(ge=0)
    rate_amount: str
    is_closed: bool = False
    min_los: int = 1
    max_los: int = 365


class InventoryPushRequest(BaseModel):
    updates: list[InventoryCell]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "dummy-ota"}


@app.get("/partner/v1/meta")
def meta() -> dict[str, Any]:
    return {
        "service": "kira-dummy-ota",
        "hotels": len(HOTELS),
        "reservations_seeded": len(RESERVATIONS),
        "ari_pushes_received": len(_ari_push_log),
    }


@app.post("/partner/v1/auth/verify")
def auth_verify(body: AuthVerifyRequest) -> dict[str, Any]:
    c = body.credentials
    if body.ota == "booking_com":
        ok = c.get("api_key") == "dummy-bdc-key" and c.get("hotel_id") == "DUMMY-BDC-001"
        name = "Grand Plaza (Dummy Booking.com)" if ok else None
    elif body.ota == "expedia":
        ok = (
            c.get("client_id") == "dummy-exp-client"
            and c.get("api_secret") == "dummy-exp-secret"
            and c.get("hotel_id") == "DUMMY-EXP-001"
        )
        name = "Seaside Inn (Dummy Expedia)" if ok else None
    else:
        ok = (
            c.get("access_key") == "dummy-mmt-access"
            and c.get("secret_key") == "dummy-mmt-secret"
            and c.get("property_id") == "DUMMY-MMT-001"
        )
        name = "Lakeview Resort (Dummy MMT)" if ok else None

    if not ok:
        raise HTTPException(status_code=401, detail="Invalid credentials for dummy OTA")
    return {
        "success": True,
        "message": "Connection successful (dummy OTA)",
        "hotel_name": name,
        "ota": body.ota,
    }


@app.get("/partner/v1/hotels")
def list_hotels() -> dict[str, Any]:
    return {"items": HOTELS, "total": len(HOTELS)}


@app.get("/partner/v1/hotels/{hotel_id}")
def get_hotel(hotel_id: str) -> dict[str, Any]:
    h = _hotel_or_404(hotel_id)
    return {**h, "room_types": ROOM_TYPES.get(hotel_id, []), "rate_plans": RATE_PLANS.get(hotel_id, [])}


@app.get("/partner/v1/hotels/{hotel_id}/room-types")
def list_room_types(hotel_id: str) -> dict[str, Any]:
    _hotel_or_404(hotel_id)
    items = ROOM_TYPES.get(hotel_id, [])
    return {"items": items, "total": len(items)}


@app.get("/partner/v1/hotels/{hotel_id}/rate-plans")
def list_rate_plans(hotel_id: str) -> dict[str, Any]:
    _hotel_or_404(hotel_id)
    items = RATE_PLANS.get(hotel_id, [])
    return {"items": items, "total": len(items)}


@app.get("/partner/v1/hotels/{hotel_id}/inventory")
def get_inventory(hotel_id: str) -> dict[str, Any]:
    _hotel_or_404(hotel_id)
    rows = inventory_snapshot(hotel_id)
    return {"hotel_id": hotel_id, "items": rows, "total": len(rows)}


@app.get("/partner/v1/hotels/{hotel_id}/reservations")
def list_reservations(
    hotel_id: str,
    since: str | None = Query(None, description="ISO date or datetime; filter by created_at >= since"),
    status: str | None = Query(None, description="Optional: confirmed | cancelled"),
) -> dict[str, Any]:
    _hotel_or_404(hotel_id)
    since_dt = _parse_since(since)
    items: list[dict[str, Any]] = []
    for r in RESERVATIONS:
        if r["hotel_id"] != hotel_id:
            continue
        if status and r["status"] != status:
            continue
        if since_dt:
            created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created < since_dt:
                continue
        items.append(r)
    return {
        "hotel_id": hotel_id,
        "items": items,
        "total": len(items),
        "since": since,
    }


@app.post("/partner/v1/hotels/{hotel_id}/inventory/push")
def push_inventory(hotel_id: str, body: InventoryPushRequest) -> dict[str, Any]:
    _hotel_or_404(hotel_id)
    entry = {
        "hotel_id": hotel_id,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "cells": len(body.updates),
        "sample": [u.model_dump() for u in body.updates[:5]],
    }
    _ari_push_log.append(entry)
    return {
        "success": True,
        "accepted": len(body.updates),
        "message": "Dummy OTA accepted ARI payload (not persisted; see GET /partner/v1/debug/ari-log)",
    }


@app.get("/partner/v1/debug/ari-log")
def ari_log(limit: int = Query(20, ge=1, le=200)) -> dict[str, Any]:
    tail = _ari_push_log[-limit:]
    return {"items": tail, "total": len(_ari_push_log)}


@app.post("/partner/v1/webhooks/echo")
def webhook_echo(payload: dict[str, Any]) -> dict[str, Any]:
    """OTA-style inbound webhook target — logs shape only."""
    return {"received": True, "keys": list(payload.keys())}
