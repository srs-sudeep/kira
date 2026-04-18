"""Tests for notification CRUD: list, unread count, mark read, mark-all-read."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ForbiddenError, NotFoundError
from app.services.notification_service import NotificationService
from tests.conftest import FAKE_USER_ID, OTHER_USER_ID, make_notification


class TestListNotifications:
    async def test_empty_when_no_notifications(self, db: AsyncSession):
        svc = NotificationService(db)
        result = await svc.list_notifications(FAKE_USER_ID)
        assert result.total == 0
        assert result.items == []
        assert result.unread == 0

    async def test_returns_only_current_user_notifications(self, db: AsyncSession):
        await make_notification(db, FAKE_USER_ID, title="Mine")
        await make_notification(db, OTHER_USER_ID, title="Not Mine")
        await db.commit()

        svc = NotificationService(db)
        result = await svc.list_notifications(FAKE_USER_ID)
        assert result.total == 1
        assert result.items[0].title == "Mine"

    async def test_paginated_results(self, db: AsyncSession):
        for i in range(5):
            await make_notification(db, FAKE_USER_ID, title=f"N{i}")
        await db.commit()

        svc = NotificationService(db)
        result = await svc.list_notifications(FAKE_USER_ID, page=1, page_size=2)
        assert result.total == 5
        assert len(result.items) == 2
        assert result.pages == 3

    async def test_filter_by_type(self, db: AsyncSession):
        await make_notification(db, type="new_booking")
        await make_notification(db, type="cancellation")
        await make_notification(db, type="channel_failure")
        await db.commit()

        svc = NotificationService(db)
        result = await svc.list_notifications(FAKE_USER_ID, type_filter=["new_booking"])
        assert result.total == 1
        assert result.items[0].type == "new_booking"

    async def test_filter_multiple_types(self, db: AsyncSession):
        await make_notification(db, type="new_booking")
        await make_notification(db, type="cancellation")
        await make_notification(db, type="system")
        await db.commit()

        svc = NotificationService(db)
        result = await svc.list_notifications(FAKE_USER_ID, type_filter=["new_booking", "cancellation"])
        assert result.total == 2

    async def test_filter_by_is_read_false(self, db: AsyncSession):
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=True)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.list_notifications(FAKE_USER_ID, is_read=False)
        assert result.total == 1
        assert result.items[0].is_read is False

    async def test_filter_by_is_read_true(self, db: AsyncSession):
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=True)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.list_notifications(FAKE_USER_ID, is_read=True)
        assert result.total == 1

    async def test_unread_count_in_list_response(self, db: AsyncSession):
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=True)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.list_notifications(FAKE_USER_ID)
        assert result.total == 3
        assert result.unread == 2

    async def test_newest_first_ordering(self, db: AsyncSession):
        n1 = await make_notification(db, title="First")
        n2 = await make_notification(db, title="Second")
        await db.commit()

        svc = NotificationService(db)
        result = await svc.list_notifications(FAKE_USER_ID)
        # Newest first
        assert result.items[0].id == n2.id
        assert result.items[1].id == n1.id


class TestUnreadCount:
    async def test_zero_when_all_read(self, db: AsyncSession):
        await make_notification(db, is_read=True)
        await make_notification(db, is_read=True)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.get_unread_count(FAKE_USER_ID)
        assert result.unread == 0

    async def test_counts_only_unread(self, db: AsyncSession):
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=True)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.get_unread_count(FAKE_USER_ID)
        assert result.unread == 2

    async def test_does_not_count_other_users(self, db: AsyncSession):
        await make_notification(db, FAKE_USER_ID, is_read=False)
        await make_notification(db, OTHER_USER_ID, is_read=False)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.get_unread_count(FAKE_USER_ID)
        assert result.unread == 1


class TestMarkRead:
    async def test_marks_unread_notification_as_read(self, db: AsyncSession):
        notif = await make_notification(db, is_read=False)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.mark_read(notif.id, FAKE_USER_ID)
        assert result.is_read is True
        assert result.read_at is not None

    async def test_idempotent_when_already_read(self, db: AsyncSession):
        notif = await make_notification(db, is_read=True)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.mark_read(notif.id, FAKE_USER_ID)
        assert result.is_read is True

    async def test_raises_not_found_for_unknown_id(self, db: AsyncSession):
        svc = NotificationService(db)
        with pytest.raises(NotFoundError):
            await svc.mark_read(uuid.uuid4(), FAKE_USER_ID)

    async def test_raises_forbidden_when_not_owner(self, db: AsyncSession):
        notif = await make_notification(db, FAKE_USER_ID, is_read=False)
        await db.commit()

        svc = NotificationService(db)
        with pytest.raises(ForbiddenError):
            await svc.mark_read(notif.id, OTHER_USER_ID)


class TestMarkAllRead:
    async def test_marks_all_unread_as_read(self, db: AsyncSession):
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=True)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.mark_all_read(FAKE_USER_ID)
        assert result.marked == 2

    async def test_returns_zero_when_nothing_to_mark(self, db: AsyncSession):
        await make_notification(db, is_read=True)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.mark_all_read(FAKE_USER_ID)
        assert result.marked == 0

    async def test_only_marks_current_users_notifications(self, db: AsyncSession):
        await make_notification(db, FAKE_USER_ID, is_read=False)
        await make_notification(db, OTHER_USER_ID, is_read=False)
        await db.commit()

        svc = NotificationService(db)
        result = await svc.mark_all_read(FAKE_USER_ID)
        assert result.marked == 1

        # Other user's notification should still be unread
        count = await svc.get_unread_count(OTHER_USER_ID)
        assert count.unread == 1


# ── HTTP routes ───────────────────────────────────────────────────────────────


class TestNotificationRoutes:
    async def test_list_route(self, client, db: AsyncSession):
        await make_notification(db)
        await db.commit()
        resp = await client.get("/api/v1/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert "unread" in data

    async def test_list_route_filter_by_type(self, client, db: AsyncSession):
        await make_notification(db, type="new_booking")
        await make_notification(db, type="cancellation")
        await db.commit()
        resp = await client.get("/api/v1/notifications?type=new_booking")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    async def test_unread_count_route(self, client, db: AsyncSession):
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=True)
        await db.commit()
        resp = await client.get("/api/v1/notifications/unread-count")
        assert resp.status_code == 200
        assert resp.json()["unread"] == 1

    async def test_mark_read_route(self, client, db: AsyncSession):
        notif = await make_notification(db, is_read=False)
        await db.commit()
        resp = await client.patch(f"/api/v1/notifications/{notif.id}/read")
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    async def test_mark_all_read_route(self, client, db: AsyncSession):
        await make_notification(db, is_read=False)
        await make_notification(db, is_read=False)
        await db.commit()
        resp = await client.post("/api/v1/notifications/mark-all-read")
        assert resp.status_code == 200
        assert resp.json()["marked"] == 2

    async def test_mark_read_not_found(self, client):
        resp = await client.patch(f"/api/v1/notifications/{uuid.uuid4()}/read")
        assert resp.status_code == 404

    async def test_pagination_params(self, client, db: AsyncSession):
        for _ in range(10):
            await make_notification(db)
        await db.commit()
        resp = await client.get("/api/v1/notifications?page=2&page_size=3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert len(data["items"]) == 3
