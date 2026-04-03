"""Seed demo tenant business data (room types, ARI, reservations, channels, etc.)."""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import asyncpg

from seed_crypto import encrypt_credentials, encrypt_pii, hash_email
from seed_sql import split_sql_statements

# Fixed namespace for deterministic FKs (reproducible seed)
_NS = uuid.UUID("00000000-0000-0000-0000-000000000001")


def nid(label: str) -> uuid.UUID:
    return uuid.uuid5(_NS, f"seed:{label}")


def get_encryption_key() -> str:
    return os.environ.get(
        "ENCRYPTION_KEY",
        "0000000000000000000000000000000000000000000000000000000000000000",
    )


async def apply_tenant_ddl(conn: asyncpg.Connection, schema: str, ddl_sql: str) -> None:
    await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    await conn.execute(f'SET search_path TO "{schema}", public')
    for stmt in split_sql_statements(ddl_sql):
        await conn.execute(stmt)


async def truncate_tenant_data(conn: asyncpg.Connection, schema: str) -> None:
    await conn.execute(f'SET search_path TO "{schema}", public')
    await conn.execute(
        """
        TRUNCATE
            sync_logs,
            channel_mappings,
            channels,
            reservation_notes,
            reservations,
            guest_profiles,
            ari_snapshots,
            seasonal_rules,
            blackout_dates,
            inventory_history,
            rate_plans,
            room_types,
            notification_preferences,
            notifications
        RESTART IDENTITY CASCADE
        """
    )


async def seed_tenant_business_data(
    conn: asyncpg.Connection,
    *,
    tenant_schema: str,
    manager_user_id: uuid.UUID,
) -> None:
    """Populate tenant schema after truncate. Idempotent via truncate-first."""
    key = get_encryption_key()
    await conn.execute(f'SET search_path TO "{tenant_schema}", public')

    # ── IDs ───────────────────────────────────────────────────────────────────
    rt_dlx = nid("room:dlx")
    rt_std = nid("room:std")
    rt_suite = nid("room:suite")

    rp_dlx_bar = nid("rp:dlx:bar")
    rp_dlx_nrf = nid("rp:dlx:nrf")
    rp_std_bar = nid("rp:std:bar")
    rp_suite_pkg = nid("rp:suite:pkg")

    ch_bdc = nid("ch:booking")
    ch_exp = nid("ch:expedia")
    ch_mmt = nid("ch:mmt")

    # ── Room types ────────────────────────────────────────────────────────────
    await conn.execute(
        """
        INSERT INTO room_types (
            id, name, description, max_occupancy, default_occupancy, bedding_type,
            amenities, images, physical_inventory, sort_order, is_active
        ) VALUES
            ($1, 'Deluxe King', 'Corner room, city view', 3, 2, 'king',
             '["wifi","minibar","tv"]'::jsonb, '[]'::jsonb, 24, 1, true),
            ($2, 'Standard Twin', 'Comfortable twin beds', 2, 2, 'twin',
             '["wifi","tv"]'::jsonb, '[]'::jsonb, 40, 2, true),
            ($3, 'Executive Suite', 'Separate living area', 4, 2, 'king',
             '["wifi","minibar","tv","bathtub"]'::jsonb, '[]'::jsonb, 8, 3, true)
        """,
        rt_dlx,
        rt_std,
        rt_suite,
    )

    # ── Rate plans ────────────────────────────────────────────────────────────
    await conn.execute(
        """
        INSERT INTO rate_plans (
            id, room_type_id, name, plan_type, base_amount, currency,
            min_los, max_los, is_active
        ) VALUES
            ($1, $2, 'Best Available Rate', 'bar', 189.00, 'USD', 1, 365, true),
            ($3, $2, 'Non-refundable', 'non_refundable', 159.00, 'USD', 1, 365, true),
            ($4, $5, 'BAR Standard', 'bar', 99.00, 'USD', 1, 365, true),
            ($6, $7, 'Suite Package', 'package', 349.00, 'USD', 2, 14, true)
        """,
        rp_dlx_bar,
        rt_dlx,
        rp_dlx_nrf,
        rp_std_bar,
        rt_std,
        rp_suite_pkg,
        rt_suite,
    )

    # ── Channels (encrypted dummy credentials) ────────────────────────────────
    cred_bdc = encrypt_credentials(
        {"api_key": "dummy-bdc-key", "hotel_id": "DUMMY-001"}, key
    )
    cred_exp = encrypt_credentials(
        {"client_id": "dummy-exp", "api_secret": "dummy-secret", "hotel_id": "EXP-1"}, key
    )
    cred_mmt = encrypt_credentials(
        {"access_key": "dummy-mmt", "secret_key": "dummy-mmt-secret", "property_id": "MMT-1"},
        key,
    )

    await conn.execute(
        """
        INSERT INTO channels (
            id, ota_code, display_name, credentials_ref, status, last_sync_at,
            error_message, consecutive_failures, config, is_active
        ) VALUES
            ($1, 'booking_com', 'Booking.com — Grand Hotel', $2, 'connected',
             NOW() - interval '2 hours', NULL, 0, '{"region":"us"}'::jsonb, true),
            ($3, 'expedia', 'Expedia Partner', $4, 'connected',
             NOW() - interval '30 minutes', NULL, 0, '{}'::jsonb, true),
            ($5, 'makemytrip', 'MakeMyTrip India', $6, 'error',
             NOW() - interval '1 day', 'Rate limit exceeded', 3, '{}'::jsonb, true)
        """,
        ch_bdc,
        cred_bdc,
        ch_exp,
        cred_exp,
        ch_mmt,
        cred_mmt,
    )

    # ── Mappings ──────────────────────────────────────────────────────────────
    await conn.execute(
        """
        INSERT INTO channel_mappings (
            channel_id, internal_room_type_id, ota_room_type_id,
            internal_rate_plan_id, ota_rate_plan_id, is_active
        ) VALUES
            ($1, $2, 'BDC-DLX', $3, 'BDC-BAR', true),
            ($4, $5, 'EXP-STD', $6, 'EXP-BAR', true),
            ($7, $8, 'MMT-SUITE', $9, 'MMT-PKG', true)
        """,
        ch_bdc,
        rt_dlx,
        rp_dlx_bar,
        ch_exp,
        rt_std,
        rp_std_bar,
        ch_mmt,
        rt_suite,
        rp_suite_pkg,
    )

    # ── ARI snapshots (90 days, key room/rate pairs) ──────────────────────────
    today = date.today()
    pairs = [
        (rt_dlx, rp_dlx_bar, Decimal("189.00")),
        (rt_dlx, rp_dlx_nrf, Decimal("159.00")),
        (rt_std, rp_std_bar, Decimal("99.00")),
        (rt_suite, rp_suite_pkg, Decimal("349.00")),
    ]
    for d in range(90):
        day = today + timedelta(days=d)
        for rt_id, rp_id, base_rate in pairs:
            avail = 8 if d % 14 != 13 else 0
            closed = d % 14 == 13
            rate = base_rate + Decimal(d % 5)
            await conn.execute(
                """
                INSERT INTO ari_snapshots (
                    room_type_id, rate_plan_id, date, available_rooms, rate_amount,
                    is_closed, min_los, max_los
                ) VALUES ($1, $2, $3, $4, $5, $6, 1, 365)
                ON CONFLICT (room_type_id, rate_plan_id, date) DO UPDATE SET
                    available_rooms = EXCLUDED.available_rooms,
                    rate_amount = EXCLUDED.rate_amount,
                    is_closed = EXCLUDED.is_closed
                """,
                rt_id,
                rp_id,
                day,
                avail,
                rate,
                closed,
            )

    # ── Seasonal + blackout ───────────────────────────────────────────────────
    await conn.execute(
        """
        INSERT INTO seasonal_rules (
            room_type_id, rate_plan_id, name, start_date, end_date,
            adjustment_type, adjustment_value, is_active
        ) VALUES
            ($1, $2, 'Summer peak', $3, $4, 'percentage', 15.0, true)
        """,
        rt_dlx,
        rp_dlx_bar,
        today + timedelta(days=60),
        today + timedelta(days=120),
    )
    await conn.execute(
        """
        INSERT INTO blackout_dates (date, reason) VALUES ($1, 'City marathon event')
        ON CONFLICT (date) DO NOTHING
        """,
        today + timedelta(days=45),
    )

    # ── Guest profiles ────────────────────────────────────────────────────────
    guests: list[tuple[uuid.UUID, str, str, str, bytes, str]] = []
    for i in range(20):
        gid = nid(f"guest:{i}")
        fn, ln, em = f"Guest{i}", f"Demo{i}", f"guest{i}.demo@example.com"
        em_hash = hash_email(em)
        em_enc = encrypt_pii(em, key)
        guests.append((gid, fn, ln, em, em_enc, em_hash))

    for gid, fn, ln, _em, em_enc, em_hash in guests:
        await conn.execute(
            """
            INSERT INTO guest_profiles (id, first_name, last_name, email, email_hash, nationality)
            VALUES ($1, $2, $3, $4, $5, 'USA')
            """,
            gid,
            fn,
            ln,
            em_enc,
            em_hash,
        )

    # ── Reservations ──────────────────────────────────────────────────────────
    sources = [
        ("booking_com", ch_bdc),
        ("expedia", ch_exp),
        ("makemytrip", ch_mmt),
        ("direct", None),
        ("manual", None),
        ("phone", None),
    ]
    statuses = ["confirmed", "confirmed", "checked_in", "checked_out", "cancelled", "confirmed"]
    rts = [(rt_dlx, rp_dlx_bar), (rt_std, rp_std_bar), (rt_suite, rp_suite_pkg)]

    for i in range(22):
        rid = nid(f"res:{i}")
        gid = guests[i % len(guests)][0]
        src, cid = sources[i % len(sources)]
        st = statuses[i % len(statuses)]
        rt_id, rp_id = rts[i % len(rts)]
        ci = today + timedelta(days=(i % 20) - 10)
        co = ci + timedelta(days=2 + (i % 4))
        total = Decimal("120.00") + Decimal(i * 17)
        conf = f"KIRA-D{i+1:05d}"[:20]
        cancelled_at = None
        cancel_reason = None
        if st == "cancelled":
            cancelled_at = datetime.now(timezone.utc)
            cancel_reason = "Guest request"

        created_at = datetime.now(timezone.utc) - timedelta(days=i % 30)
        await conn.execute(
            """
            INSERT INTO reservations (
                id, confirmation_number, channel_id, source, room_type_id, rate_plan_id,
                check_in, check_out, guest_profile_id, adults, children, total_amount,
                currency, status, cancelled_at, cancellation_reason, channel_reservation_id,
                special_requests, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, 2, 0, $10, 'USD', $11, $12, $13,
                $14, $15, $16
            )
            """,
            rid,
            conf,
            cid,
            src,
            rt_id,
            rp_id,
            ci,
            co,
            gid,
            total,
            st,
            cancelled_at,
            cancel_reason,
            f"OTA-{i}-REF" if cid else None,
            "Late checkout please" if i % 3 == 0 else None,
            created_at,
        )

    # Notes (first 3 reservations)
    for i in range(3):
        r = nid(f"res:{i}")
        await conn.execute(
            """
            INSERT INTO reservation_notes (reservation_id, user_id, content)
            VALUES ($1, $2, $3)
            """,
            r,
            manager_user_id,
            "VIP guest — welcome amenity requested.",
        )

    # Inventory history sample
    await conn.execute(
        """
        INSERT INTO inventory_history (
            room_type_id, rate_plan_id, date, field_changed, old_value, new_value, changed_by
        ) VALUES ($1, $2, $3, 'rate_amount', '189.00', '199.00', $4)
        """,
        rt_dlx,
        rp_dlx_bar,
        today,
        manager_user_id,
    )

    # ── Sync logs ─────────────────────────────────────────────────────────────
    for i in range(15):
        ch = [ch_bdc, ch_exp, ch_mmt][i % 3]
        ev = ["ari_push", "booking_pull", "error"][i % 3]
        direction = "outbound" if ev in ("ari_push", "error") else "inbound"
        st = "success" if i % 5 != 0 else "failed"
        await conn.execute(
            """
            INSERT INTO sync_logs (
                channel_id, event_type, direction, response_status, status,
                request_summary, response_summary, retry_count, created_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                '{"cells":12}'::jsonb,
                '{"ok":true}'::jsonb,
                0,
                NOW() - ($6 * interval '1 hour')
            )
            """,
            ch,
            ev,
            direction,
            200 if st == "success" else 503,
            st,
            i * 3,
        )

    # ── Notifications (tenant schema) ───────────────────────────────────────
    notif_types = [
        ("new_booking", "New booking", "Reservation KIRA-D00001 confirmed."),
        ("channel_failure", "Channel sync issue", "MakeMyTrip push failed — retry scheduled."),
        ("low_inventory", "Low inventory", "Deluxe King below threshold for next week."),
        ("system", "Maintenance", "Rate plan cache refreshed."),
    ]
    for i, (nt, title, msg) in enumerate(notif_types * 2):
        await conn.execute(
            """
            INSERT INTO notifications (user_id, type, title, message, data, is_read, created_at)
            VALUES ($1, $2, $3, $4, '{}'::jsonb, $5, NOW() - ($6::integer * interval '1 day'))
            """,
            manager_user_id,
            nt,
            title,
            msg,
            i % 3 == 0,
            i % 5,
        )

    print(f"  Tenant data seeded in {tenant_schema} (room types, ARI, reservations, channels, …).")
