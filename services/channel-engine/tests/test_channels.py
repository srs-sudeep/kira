"""Tests for channel CRUD, mappings, sync log, health dashboard, manual sync."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.schemas.channel import ChannelCreate, ChannelUpdate
from app.schemas.mapping import MappingCreate, MappingUpdate
from app.services.channel_service import ChannelService
from tests.conftest import FAKE_TENANT_ID, make_channel, make_mapping

ROOM_TYPE_ID = uuid.uuid4()
RATE_PLAN_ID = uuid.uuid4()


# ── Channel CRUD ──────────────────────────────────────────────────────────────

class TestCreateChannel:
    async def test_create_channel_test_connection_success(self, db: AsyncSession):
        with patch("app.services.channel_service.get_adapter") as mock_get:
            mock_adapter = AsyncMock()
            mock_adapter.test_connection = AsyncMock(return_value=True)
            mock_get.return_value = mock_adapter

            svc = ChannelService(db)
            result = await svc.create_channel(
                ChannelCreate(
                    ota_code="booking_com",
                    display_name="Booking.com",
                    credentials={"api_key": "key123", "hotel_id": "H001"},
                )
            )

        assert result.status == "connected"
        assert result.ota_code == "booking_com"
        assert result.consecutive_failures == 0

    async def test_create_channel_test_connection_failure(self, db: AsyncSession):
        with patch("app.services.channel_service.get_adapter") as mock_get:
            mock_adapter = AsyncMock()
            mock_adapter.test_connection = AsyncMock(return_value=False)
            mock_get.return_value = mock_adapter

            svc = ChannelService(db)
            result = await svc.create_channel(
                ChannelCreate(
                    ota_code="expedia",
                    display_name="Expedia",
                    credentials={"client_id": "bad", "api_secret": "bad", "hotel_id": "H001"},
                )
            )

        assert result.status == "error"
        assert result.error_message is not None

    async def test_create_channel_credentials_are_encrypted(self, db: AsyncSession):
        with patch("app.services.channel_service.get_adapter") as mock_get:
            mock_adapter = AsyncMock()
            mock_adapter.test_connection = AsyncMock(return_value=True)
            mock_get.return_value = mock_adapter

            svc = ChannelService(db)
            result = await svc.create_channel(
                ChannelCreate(
                    ota_code="makemytrip",
                    display_name="MakeMyTrip",
                    credentials={"access_key": "secret", "property_id": "MMT001"},
                )
            )

        # Fetch raw channel from DB and verify credentials are bytes (encrypted)
        from app.repositories.channel_repo import ChannelRepository
        repo = ChannelRepository(db)
        channel = await repo.get_by_id(result.id)
        assert isinstance(channel.credentials_ref, bytes)

        # Decrypt and verify
        from app.core.crypto import decrypt_credentials
        decrypted = decrypt_credentials(channel.credentials_ref)
        assert decrypted["access_key"] == "secret"


class TestGetChannel:
    async def test_get_existing_channel(self, db: AsyncSession):
        channel = await make_channel(db, display_name="Test OTA")
        await db.commit()

        svc = ChannelService(db)
        result = await svc.get_channel(channel.id)
        assert result.id == channel.id
        assert result.display_name == "Test OTA"

    async def test_get_nonexistent_raises(self, db: AsyncSession):
        svc = ChannelService(db)
        with pytest.raises(NotFoundError):
            await svc.get_channel(uuid.uuid4())


class TestListChannels:
    async def test_returns_all_channels(self, db: AsyncSession):
        await make_channel(db, display_name="A")
        await make_channel(db, ota_code="expedia", display_name="B")
        await db.commit()

        svc = ChannelService(db)
        result = await svc.list_channels()
        assert result.total == 2

    async def test_returns_empty_when_none(self, db: AsyncSession):
        svc = ChannelService(db)
        result = await svc.list_channels()
        assert result.total == 0


class TestUpdateChannel:
    async def test_update_display_name(self, db: AsyncSession):
        channel = await make_channel(db, display_name="Old Name")
        await db.commit()

        svc = ChannelService(db)
        result = await svc.update_channel(channel.id, ChannelUpdate(display_name="New Name"))
        assert result.display_name == "New Name"

    async def test_update_credentials_reruns_test_connection(self, db: AsyncSession):
        channel = await make_channel(db, status="error")
        await db.commit()

        with patch("app.services.channel_service.get_adapter") as mock_get:
            mock_adapter = AsyncMock()
            mock_adapter.test_connection = AsyncMock(return_value=True)
            mock_get.return_value = mock_adapter

            svc = ChannelService(db)
            result = await svc.update_channel(
                channel.id,
                ChannelUpdate(credentials={"api_key": "new-key", "hotel_id": "H001"}),
            )

        assert result.status == "connected"
        assert result.consecutive_failures == 0

    async def test_update_nonexistent_raises(self, db: AsyncSession):
        svc = ChannelService(db)
        with pytest.raises(NotFoundError):
            await svc.update_channel(uuid.uuid4(), ChannelUpdate(display_name="X"))

    async def test_update_no_fields_returns_unchanged(self, db: AsyncSession):
        channel = await make_channel(db, display_name="Unchanged")
        await db.commit()

        svc = ChannelService(db)
        result = await svc.update_channel(channel.id, ChannelUpdate())
        assert result.display_name == "Unchanged"


class TestDeleteChannel:
    async def test_delete_sets_inactive(self, db: AsyncSession):
        channel = await make_channel(db, status="connected")
        await db.commit()

        svc = ChannelService(db)
        await svc.delete_channel(channel.id)

        from app.repositories.channel_repo import ChannelRepository
        repo = ChannelRepository(db)
        ch = await repo.get_by_id(channel.id)
        assert ch.is_active is False
        assert ch.status == "disconnected"

    async def test_delete_nonexistent_raises(self, db: AsyncSession):
        svc = ChannelService(db)
        with pytest.raises(NotFoundError):
            await svc.delete_channel(uuid.uuid4())


# ── Health dashboard ──────────────────────────────────────────────────────────

class TestHealthDashboard:
    async def test_health_dashboard_empty(self, db: AsyncSession):
        svc = ChannelService(db)
        result = await svc.get_health_dashboard()
        assert result.total == 0
        assert result.connected == 0
        assert result.channels == []

    async def test_health_dashboard_counts_statuses(self, db: AsyncSession):
        await make_channel(db, status="connected")
        await make_channel(db, ota_code="expedia", status="connected")
        await make_channel(db, ota_code="makemytrip", status="error")
        await db.commit()

        svc = ChannelService(db)
        result = await svc.get_health_dashboard()
        assert result.total == 3
        assert result.connected == 2
        assert result.error == 1
        assert len(result.channels) == 3


# ── Sync log ──────────────────────────────────────────────────────────────────

class TestSyncLog:
    async def test_sync_log_empty_for_new_channel(self, db: AsyncSession):
        channel = await make_channel(db)
        await db.commit()

        svc = ChannelService(db)
        result = await svc.get_sync_log(channel.id)
        assert result.total == 0
        assert result.items == []

    async def test_sync_log_paginated(self, db: AsyncSession):
        channel = await make_channel(db)
        await db.commit()

        from app.repositories.sync_log_repo import SyncLogRepository
        repo = SyncLogRepository(db)
        for i in range(5):
            await repo.create(
                channel_id=channel.id,
                event_type="ari_push",
                direction="outbound",
                status="success",
            )
        await db.commit()

        svc = ChannelService(db)
        result = await svc.get_sync_log(channel.id, page=1, page_size=2)
        assert result.total == 5
        assert len(result.items) == 2
        assert result.pages == 3

    async def test_sync_log_nonexistent_channel_raises(self, db: AsyncSession):
        svc = ChannelService(db)
        with pytest.raises(NotFoundError):
            await svc.get_sync_log(uuid.uuid4())


# ── Channel mappings ──────────────────────────────────────────────────────────

class TestChannelMappings:
    async def test_create_mapping(self, db: AsyncSession):
        channel = await make_channel(db)
        await db.commit()

        svc = ChannelService(db)
        result = await svc.create_mapping(
            channel.id,
            MappingCreate(
                internal_room_type_id=ROOM_TYPE_ID,
                ota_room_type_id="BDC_STANDARD",
                internal_rate_plan_id=RATE_PLAN_ID,
                ota_rate_plan_id="BDC_BAR",
            ),
        )
        assert result.channel_id == channel.id
        assert result.ota_room_type_id == "BDC_STANDARD"

    async def test_create_duplicate_mapping_raises(self, db: AsyncSession):
        channel = await make_channel(db)
        room_type_id = uuid.uuid4()
        rate_plan_id = uuid.uuid4()
        await make_mapping(
            db, channel.id,
            internal_room_type_id=room_type_id,
            internal_rate_plan_id=rate_plan_id,
        )
        await db.commit()

        svc = ChannelService(db)
        with pytest.raises(ConflictError):
            await svc.create_mapping(
                channel.id,
                MappingCreate(
                    internal_room_type_id=room_type_id,
                    ota_room_type_id="OTA_RT",
                    internal_rate_plan_id=rate_plan_id,
                    ota_rate_plan_id="OTA_RP",
                ),
            )

    async def test_list_mappings(self, db: AsyncSession):
        channel = await make_channel(db)
        await make_mapping(db, channel.id)
        await make_mapping(db, channel.id, ota_room_type_id="RT_DELUXE", ota_rate_plan_id="RP_NR")
        await db.commit()

        svc = ChannelService(db)
        result = await svc.list_mappings(channel.id)
        assert result.total == 2

    async def test_update_mapping(self, db: AsyncSession):
        channel = await make_channel(db)
        mapping = await make_mapping(db, channel.id, ota_room_type_id="OLD_RT")
        await db.commit()

        svc = ChannelService(db)
        result = await svc.update_mapping(
            channel.id, mapping.id, MappingUpdate(ota_room_type_id="NEW_RT")
        )
        assert result.ota_room_type_id == "NEW_RT"

    async def test_delete_mapping(self, db: AsyncSession):
        channel = await make_channel(db)
        mapping = await make_mapping(db, channel.id)
        await db.commit()

        svc = ChannelService(db)
        await svc.delete_mapping(channel.id, mapping.id)

        result = await svc.list_mappings(channel.id)
        assert result.total == 0

    async def test_delete_mapping_wrong_channel_raises(self, db: AsyncSession):
        ch1 = await make_channel(db, display_name="CH1")
        ch2 = await make_channel(db, ota_code="expedia", display_name="CH2")
        mapping = await make_mapping(db, ch1.id)
        await db.commit()

        svc = ChannelService(db)
        with pytest.raises(NotFoundError):
            # Try to delete ch1's mapping using ch2's ID
            await svc.delete_mapping(ch2.id, mapping.id)


# ── HTTP routes ───────────────────────────────────────────────────────────────

class TestChannelRoutes:
    async def test_get_health_route(self, client):
        resp = await client.get("/api/v1/channels/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "channels" in data

    async def test_list_channels_route(self, client):
        resp = await client.get("/api/v1/channels")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_create_channel_route(self, client):
        with patch("app.services.channel_service.get_adapter") as mock_get:
            mock_adapter = AsyncMock()
            mock_adapter.test_connection = AsyncMock(return_value=True)
            mock_get.return_value = mock_adapter

            resp = await client.post(
                "/api/v1/channels",
                json={
                    "ota_code": "booking_com",
                    "display_name": "Booking.com Test",
                    "credentials": {"api_key": "k", "hotel_id": "H"},
                },
            )
        assert resp.status_code == 201
        assert resp.json()["status"] == "connected"

    async def test_get_channel_route_not_found(self, client):
        resp = await client.get(f"/api/v1/channels/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_delete_channel_route(self, client, db: AsyncSession):
        channel = await make_channel(db)
        await db.commit()

        resp = await client.delete(f"/api/v1/channels/{channel.id}")
        assert resp.status_code == 204

    async def test_create_mapping_route(self, client, db: AsyncSession):
        channel = await make_channel(db)
        await db.commit()

        resp = await client.post(
            f"/api/v1/channels/{channel.id}/mapping",
            json={
                "internal_room_type_id": str(ROOM_TYPE_ID),
                "ota_room_type_id": "BDC_STD",
                "internal_rate_plan_id": str(RATE_PLAN_ID),
                "ota_rate_plan_id": "BDC_BAR",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["ota_room_type_id"] == "BDC_STD"

    async def test_sync_log_route(self, client, db: AsyncSession):
        channel = await make_channel(db)
        await db.commit()

        resp = await client.get(f"/api/v1/channels/{channel.id}/sync-log")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
