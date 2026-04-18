"""Tests for room type CRUD."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.schemas.room_type import RoomTypeCreate, RoomTypeUpdate
from app.services.room_type_service import RoomTypeService
from tests.conftest import make_room_type


class TestRoomTypeService:
    async def test_create_room_type(self, db: AsyncSession):
        svc = RoomTypeService(db)
        req = RoomTypeCreate(
            name="Deluxe Suite",
            max_occupancy=3,
            default_occupancy=2,
            physical_inventory=5,
        )
        result = await svc.create(req)
        assert result.name == "Deluxe Suite"
        assert result.physical_inventory == 5
        assert result.is_active is True

    async def test_list_returns_active_only(self, db: AsyncSession):
        await make_room_type(db, name="Active Room", is_active=True)
        await make_room_type(db, name="Inactive Room", is_active=False)
        svc = RoomTypeService(db)
        result = await svc.list()
        names = [r.name for r in result.items]
        assert "Active Room" in names
        assert "Inactive Room" not in names

    async def test_get_by_id(self, db: AsyncSession):
        rt = await make_room_type(db, name="Standard Room")
        svc = RoomTypeService(db)
        result = await svc.get(rt.id)
        assert result.id == rt.id
        assert result.name == "Standard Room"

    async def test_get_nonexistent_raises(self, db: AsyncSession):
        svc = RoomTypeService(db)
        with pytest.raises(NotFoundError):
            await svc.get(uuid.uuid4())

    async def test_update_partial(self, db: AsyncSession):
        rt = await make_room_type(db, name="Old Name")
        svc = RoomTypeService(db)
        result = await svc.update(rt.id, RoomTypeUpdate(name="New Name"))
        assert result.name == "New Name"
        assert result.physical_inventory == rt.physical_inventory  # unchanged

    async def test_update_nonexistent_raises(self, db: AsyncSession):
        svc = RoomTypeService(db)
        with pytest.raises(NotFoundError):
            await svc.update(uuid.uuid4(), RoomTypeUpdate(name="X"))

    async def test_delete_soft(self, db: AsyncSession):
        rt = await make_room_type(db)
        svc = RoomTypeService(db)
        await svc.delete(rt.id)
        with pytest.raises(NotFoundError):
            await svc.get(rt.id)

    async def test_delete_nonexistent_raises(self, db: AsyncSession):
        svc = RoomTypeService(db)
        with pytest.raises(NotFoundError):
            await svc.delete(uuid.uuid4())

    async def test_pagination(self, db: AsyncSession):
        for i in range(5):
            await make_room_type(db, name=f"Room {i}")
        svc = RoomTypeService(db)
        page1 = await svc.list(page=1, page_size=3)
        page2 = await svc.list(page=2, page_size=3)
        assert len(page1.items) == 3
        assert page1.total == 5
        assert page1.pages == 2
        assert len(page2.items) == 2

    async def test_amenities_and_images_stored(self, db: AsyncSession):
        svc = RoomTypeService(db)
        req = RoomTypeCreate(
            name="Premium Room",
            max_occupancy=2,
            default_occupancy=2,
            physical_inventory=3,
            amenities=["wifi", "minibar", "safe"],
            images=[{"url": "https://example.com/img.jpg", "alt": "Room view"}],
        )
        result = await svc.create(req)
        assert result.amenities == ["wifi", "minibar", "safe"]
        assert len(result.images) == 1


class TestRoomTypeRoutes:
    async def test_list_returns_200(self, client):
        resp = await client.get("/api/v1/rooms/types")
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_create_returns_201(self, client):
        resp = await client.post(
            "/api/v1/rooms/types",
            json={"name": "Test Room", "max_occupancy": 2, "default_occupancy": 2, "physical_inventory": 5},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Test Room"

    async def test_get_existing(self, client, db: AsyncSession):
        rt = await make_room_type(db, name="Fetch Me")
        resp = await client.get(f"/api/v1/rooms/types/{rt.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Fetch Me"

    async def test_get_404(self, client):
        resp = await client.get(f"/api/v1/rooms/types/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_patch(self, client, db: AsyncSession):
        rt = await make_room_type(db, name="Before")
        resp = await client.patch(f"/api/v1/rooms/types/{rt.id}", json={"name": "After"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "After"

    async def test_delete(self, client, db: AsyncSession):
        rt = await make_room_type(db)
        resp = await client.delete(f"/api/v1/rooms/types/{rt.id}")
        assert resp.status_code == 204
