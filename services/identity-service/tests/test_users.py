"""Tests for user management: list, invite, update, delete."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.user import User
from app.schemas.user import InviteUserRequest, UpdateUserRequest
from app.services.user_service import UserService
from tests.conftest import auth_headers, make_user


def _make_service(session: AsyncSession) -> UserService:
    return UserService(session)


# ── list_users ────────────────────────────────────────────────────────────────

class TestListUsers:
    async def test_list_returns_tenant_users(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(db_session, email="owner@t.com", role="property_owner", tenant_id=tenant_id)
        await make_user(db_session, email="staff@t.com", role="front_desk", tenant_id=tenant_id)

        svc = _make_service(db_session)
        result = await svc.list_users(tenant_id=tenant_id, page=1, page_size=10)
        assert result.total == 2
        assert len(result.items) == 2

    async def test_list_excludes_other_tenant_users(
        self, db_session: AsyncSession
    ):
        t1 = uuid.uuid4()
        t2 = uuid.uuid4()
        await make_user(db_session, email="a@t1.com", tenant_id=t1)
        await make_user(db_session, email="b@t2.com", tenant_id=t2)

        svc = _make_service(db_session)
        result = await svc.list_users(tenant_id=t1, page=1, page_size=10)
        assert result.total == 1
        assert result.items[0].email == "a@t1.com"

    async def test_pagination_respects_page_size(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(db_session, email="pg0@t.com", tenant_id=tenant_id)
        for i in range(5):
            await make_user(db_session, email=f"pg{i+1}@t.com", tenant_id=tenant_id)

        svc = _make_service(db_session)
        result = await svc.list_users(tenant_id=tenant_id, page=1, page_size=3)
        assert len(result.items) == 3
        assert result.pages == 2


# ── invite_user ───────────────────────────────────────────────────────────────

class TestInviteUser:
    @pytest.fixture
    async def owner(self, db_session: AsyncSession, tenant_id: uuid.UUID) -> User:
        return await make_user(db_session, email="owner@inv.com", role="property_owner", tenant_id=tenant_id)

    async def test_invite_creates_new_user(
        self, db_session: AsyncSession, owner: User, tenant_id: uuid.UUID
    ):
        svc = _make_service(db_session)
        req = InviteUserRequest(
            email="invited@example.com",
            first_name="Inv",
            last_name="User",
            role="front_desk",
        )
        # Patch the Celery task so no broker is needed in tests
        from unittest.mock import MagicMock, patch
        with patch("app.services.user_service.send_invite_email") as mock_task:
            mock_task.delay = MagicMock()
            user = await svc.invite_user(req, actor=owner)

        assert user.email == "invited@example.com"
        assert user.role == "front_desk"
        assert user.tenant_id == tenant_id

    async def test_invite_duplicate_email_raises(
        self, db_session: AsyncSession, owner: User, tenant_id: uuid.UUID
    ):
        await make_user(db_session, email="dup@example.com", tenant_id=tenant_id)
        svc = _make_service(db_session)
        req = InviteUserRequest(
            email="dup@example.com",
            first_name="D",
            last_name="Up",
            role="front_desk",
        )
        with pytest.raises(ConflictError):
            await svc.invite_user(req, actor=owner)

    async def test_front_desk_cannot_invite(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        fd = await make_user(db_session, email="fd@t.com", role="front_desk", tenant_id=tenant_id)
        svc = _make_service(db_session)
        req = InviteUserRequest(
            email="new@example.com", first_name="N", last_name="U", role="front_desk"
        )
        with pytest.raises(ForbiddenError):
            await svc.invite_user(req, actor=fd)


# ── update_user ───────────────────────────────────────────────────────────────

class TestUpdateUser:
    async def test_owner_can_update_same_tenant_user(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(db_session, email="own@t.com", role="property_owner", tenant_id=tenant_id)
        target = await make_user(db_session, email="tgt@t.com", role="front_desk", tenant_id=tenant_id)

        svc = _make_service(db_session)
        updated = await svc.update_user(
            target.id, UpdateUserRequest(first_name="Updated"), actor=owner
        )
        assert updated.first_name == "Updated"

    async def test_cannot_update_user_in_other_tenant(
        self, db_session: AsyncSession
    ):
        t1, t2 = uuid.uuid4(), uuid.uuid4()
        owner = await make_user(db_session, email="own@t1.com", role="property_owner", tenant_id=t1)
        other = await make_user(db_session, email="oth@t2.com", tenant_id=t2)

        svc = _make_service(db_session)
        with pytest.raises(ForbiddenError):
            await svc.update_user(other.id, UpdateUserRequest(first_name="X"), actor=owner)

    async def test_update_nonexistent_user_raises(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(db_session, role="property_owner", tenant_id=tenant_id)
        svc = _make_service(db_session)
        with pytest.raises(NotFoundError):
            await svc.update_user(uuid.uuid4(), UpdateUserRequest(first_name="X"), actor=owner)


# ── delete_user ───────────────────────────────────────────────────────────────

class TestDeleteUser:
    async def test_owner_can_delete_user(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(db_session, email="own@del.com", role="property_owner", tenant_id=tenant_id)
        target = await make_user(db_session, email="del@del.com", tenant_id=tenant_id)

        svc = _make_service(db_session)
        await svc.delete_user(target.id, actor=owner)
        assert target.is_active is False

    async def test_cannot_delete_self(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(db_session, email="self@del.com", role="property_owner", tenant_id=tenant_id)
        svc = _make_service(db_session)
        with pytest.raises(ForbiddenError):
            await svc.delete_user(owner.id, actor=owner)

    async def test_delete_nonexistent_raises(
        self, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(db_session, role="property_owner", tenant_id=tenant_id)
        svc = _make_service(db_session)
        with pytest.raises(NotFoundError):
            await svc.delete_user(uuid.uuid4(), actor=owner)


# ── HTTP integration tests ────────────────────────────────────────────────────

class TestUserRoutes:
    async def test_list_users_requires_auth(self, client):
        resp = await client.get("/api/v1/users/")
        assert resp.status_code == 401

    async def test_list_users_forbidden_for_front_desk(
        self, client, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        fd = await make_user(db_session, email="fd@route.com", role="front_desk", tenant_id=tenant_id)
        resp = await client.get("/api/v1/users/", headers=auth_headers(fd))
        assert resp.status_code == 403

    async def test_list_users_ok_for_owner(
        self, client, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(
            db_session, email="own@route.com", role="property_owner", tenant_id=tenant_id
        )
        resp = await client.get("/api/v1/users/", headers=auth_headers(owner))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total"] >= 1

    async def test_get_user_by_id(
        self, client, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(
            db_session, email="own2@route.com", role="property_owner", tenant_id=tenant_id
        )
        resp = await client.get(
            f"/api/v1/users/{owner.id}", headers=auth_headers(owner)
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(owner.id)

    async def test_patch_user(
        self, client, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(
            db_session, email="patch@route.com", role="property_owner", tenant_id=tenant_id
        )
        target = await make_user(
            db_session, email="tgt2@route.com", role="front_desk", tenant_id=tenant_id
        )
        resp = await client.patch(
            f"/api/v1/users/{target.id}",
            json={"first_name": "Patched"},
            headers=auth_headers(owner),
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Patched"

    async def test_delete_user(
        self, client, db_session: AsyncSession, tenant_id: uuid.UUID
    ):
        owner = await make_user(
            db_session, email="del2@route.com", role="property_owner", tenant_id=tenant_id
        )
        target = await make_user(
            db_session, email="tgt3@route.com", role="front_desk", tenant_id=tenant_id
        )
        resp = await client.delete(
            f"/api/v1/users/{target.id}", headers=auth_headers(owner)
        )
        assert resp.status_code == 204
