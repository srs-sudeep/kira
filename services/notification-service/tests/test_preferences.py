"""Tests for notification preferences: get defaults, upsert, respect in consumer."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.preference_repo import ALL_EVENT_TYPES, PreferenceRepository
from app.schemas.preference import PreferenceUpsert, PreferencesUpdateRequest
from app.services.notification_service import NotificationService
from tests.conftest import FAKE_USER_ID, make_preference


class TestGetPreferences:
    async def test_returns_defaults_when_no_preferences_saved(self, db: AsyncSession):
        svc = NotificationService(db)
        result = await svc.get_preferences(FAKE_USER_ID)
        assert result.user_id == FAKE_USER_ID
        # Should cover all known event types
        assert len(result.items) == len(ALL_EVENT_TYPES)
        event_types = {p.event_type for p in result.items}
        assert event_types == set(ALL_EVENT_TYPES)
        # All defaults enabled
        for pref in result.items:
            assert pref.email_enabled is True
            assert pref.in_app_enabled is True

    async def test_returns_saved_preferences_merged_with_defaults(self, db: AsyncSession):
        await make_preference(
            db, event_type="new_booking", email_enabled=False, in_app_enabled=True
        )
        await db.commit()

        svc = NotificationService(db)
        result = await svc.get_preferences(FAKE_USER_ID)

        # Should still have all event types
        assert len(result.items) == len(ALL_EVENT_TYPES)

        new_booking_pref = next(p for p in result.items if p.event_type == "new_booking")
        assert new_booking_pref.email_enabled is False
        assert new_booking_pref.in_app_enabled is True

        # Other types should have defaults
        cancellation_pref = next(p for p in result.items if p.event_type == "cancellation")
        assert cancellation_pref.email_enabled is True


class TestUpdatePreferences:
    async def test_upsert_creates_new_preference(self, db: AsyncSession):
        svc = NotificationService(db)
        result = await svc.update_preferences(
            FAKE_USER_ID,
            PreferencesUpdateRequest(
                preferences=[
                    PreferenceUpsert(
                        event_type="new_booking",
                        email_enabled=False,
                        in_app_enabled=True,
                    )
                ]
            ),
        )
        new_booking = next(p for p in result.items if p.event_type == "new_booking")
        assert new_booking.email_enabled is False

    async def test_upsert_updates_existing_preference(self, db: AsyncSession):
        await make_preference(db, event_type="cancellation", email_enabled=True)
        await db.commit()

        svc = NotificationService(db)
        await svc.update_preferences(
            FAKE_USER_ID,
            PreferencesUpdateRequest(
                preferences=[
                    PreferenceUpsert(
                        event_type="cancellation",
                        email_enabled=False,
                        in_app_enabled=False,
                    )
                ]
            ),
        )
        repo = PreferenceRepository(db)
        pref = await repo.get(FAKE_USER_ID, "cancellation")
        assert pref.email_enabled is False
        assert pref.in_app_enabled is False

    async def test_upsert_multiple_preferences(self, db: AsyncSession):
        svc = NotificationService(db)
        result = await svc.update_preferences(
            FAKE_USER_ID,
            PreferencesUpdateRequest(
                preferences=[
                    PreferenceUpsert(event_type="new_booking", email_enabled=False, in_app_enabled=True),
                    PreferenceUpsert(event_type="channel_failure", email_enabled=True, in_app_enabled=False),
                ]
            ),
        )
        prefs = {p.event_type: p for p in result.items}
        assert prefs["new_booking"].email_enabled is False
        assert prefs["channel_failure"].in_app_enabled is False

    async def test_returns_full_list_after_update(self, db: AsyncSession):
        svc = NotificationService(db)
        result = await svc.update_preferences(
            FAKE_USER_ID,
            PreferencesUpdateRequest(
                preferences=[PreferenceUpsert(event_type="system", email_enabled=False)]
            ),
        )
        # All event types still covered
        assert len(result.items) == len(ALL_EVENT_TYPES)


class TestPreferenceRepository:
    async def test_is_enabled_defaults_true_when_no_record(self, db: AsyncSession):
        repo = PreferenceRepository(db)
        assert await repo.is_enabled(FAKE_USER_ID, "new_booking", "email") is True
        assert await repo.is_enabled(FAKE_USER_ID, "new_booking", "in_app") is True

    async def test_is_enabled_respects_saved_preference(self, db: AsyncSession):
        await make_preference(
            db, event_type="cancellation", email_enabled=False, in_app_enabled=True
        )
        await db.commit()

        repo = PreferenceRepository(db)
        assert await repo.is_enabled(FAKE_USER_ID, "cancellation", "email") is False
        assert await repo.is_enabled(FAKE_USER_ID, "cancellation", "in_app") is True

    async def test_upsert_is_idempotent(self, db: AsyncSession):
        repo = PreferenceRepository(db)
        await repo.upsert(FAKE_USER_ID, "system", email_enabled=True, in_app_enabled=True)
        await repo.upsert(FAKE_USER_ID, "system", email_enabled=False, in_app_enabled=False)
        await db.commit()

        # Should only have one record
        prefs = await repo.list_for_user(FAKE_USER_ID)
        system_prefs = [p for p in prefs if p.event_type == "system"]
        assert len(system_prefs) == 1
        assert system_prefs[0].email_enabled is False


# ── HTTP routes ───────────────────────────────────────────────────────────────

class TestPreferencesRoutes:
    async def test_get_preferences_route(self, client):
        resp = await client.get("/api/v1/notifications/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        assert "items" in data
        assert len(data["items"]) == len(ALL_EVENT_TYPES)

    async def test_update_preferences_route(self, client):
        resp = await client.patch(
            "/api/v1/notifications/preferences",
            json={
                "preferences": [
                    {"event_type": "new_booking", "email_enabled": False, "in_app_enabled": True},
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        new_booking = next(p for p in data["items"] if p["event_type"] == "new_booking")
        assert new_booking["email_enabled"] is False

    async def test_update_then_get_preferences(self, client):
        await client.patch(
            "/api/v1/notifications/preferences",
            json={
                "preferences": [
                    {"event_type": "channel_failure", "email_enabled": False, "in_app_enabled": False},
                ]
            },
        )
        resp = await client.get("/api/v1/notifications/preferences")
        data = resp.json()
        channel_pref = next(p for p in data["items"] if p["event_type"] == "channel_failure")
        assert channel_pref["email_enabled"] is False
        assert channel_pref["in_app_enabled"] is False
