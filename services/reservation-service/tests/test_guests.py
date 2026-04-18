"""Tests for guest PII encryption, decryption, and guest profile operations."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_pii, encrypt_pii, hash_email
from app.repositories.guest_repo import GuestRepository
from tests.conftest import make_guest


class TestCrypto:
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "guest@example.com"
        ciphertext = encrypt_pii(plaintext)
        assert isinstance(ciphertext, bytes)
        assert ciphertext != plaintext.encode()
        assert decrypt_pii(ciphertext) == plaintext

    def test_different_nonces_each_encrypt(self):
        plaintext = "same@example.com"
        ct1 = encrypt_pii(plaintext)
        ct2 = encrypt_pii(plaintext)
        # Two encryptions of the same plaintext must produce different ciphertext (random nonce)
        assert ct1 != ct2
        # But both decrypt to the same value
        assert decrypt_pii(ct1) == plaintext
        assert decrypt_pii(ct2) == plaintext

    def test_hash_email_is_deterministic(self):
        h1 = hash_email("Guest@Example.COM")
        h2 = hash_email("guest@example.com")
        # Both normalise to lowercase before hashing
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest length

    def test_hash_email_differs_for_different_emails(self):
        assert hash_email("alice@example.com") != hash_email("bob@example.com")

    def test_encrypt_non_ascii(self):
        plaintext = "über@straße.de"
        assert decrypt_pii(encrypt_pii(plaintext)) == plaintext

    def test_empty_string_roundtrip(self):
        assert decrypt_pii(encrypt_pii("")) == ""


class TestGuestRepository:
    async def test_create_guest_without_email(self, db: AsyncSession):
        repo = GuestRepository(db)
        guest = await repo.create(
            first_name="John",
            last_name="Doe",
            email_encrypted=None,
            phone_encrypted=None,
            email_hash=None,
            nationality="IN",
            preferences={},
        )
        assert guest.id is not None
        assert guest.first_name == "John"
        assert guest.email is None
        assert guest.email_hash is None

    async def test_create_guest_with_encrypted_email(self, db: AsyncSession):
        email = "test@hotel.com"
        email_hash = hash_email(email)
        email_enc = encrypt_pii(email)

        repo = GuestRepository(db)
        guest = await repo.create(
            first_name="Jane",
            last_name="Doe",
            email_encrypted=email_enc,
            phone_encrypted=None,
            email_hash=email_hash,
            nationality="US",
            preferences={"room": "high floor"},
        )
        assert guest.email_hash == email_hash
        assert guest.email is not None
        # Stored bytes should decrypt back to original email
        assert decrypt_pii(guest.email) == email

    async def test_get_by_email_hash_returns_guest(self, db: AsyncSession):
        email = "lookup@hotel.com"
        email_hash = hash_email(email)
        await make_guest(
            db,
            first_name="Eve",
            last_name="Moon",
            email_hash=email_hash,
            email_encrypted=encrypt_pii(email),
        )
        await db.commit()

        repo = GuestRepository(db)
        found = await repo.get_by_email_hash(email_hash)
        assert found is not None
        assert found.first_name == "Eve"

    async def test_get_by_email_hash_returns_none_for_unknown(self, db: AsyncSession):
        repo = GuestRepository(db)
        result = await repo.get_by_email_hash("nonexistenthash" * 4)
        assert result is None

    async def test_get_by_email_hash_returns_latest_for_duplicate_hashes(self, db: AsyncSession):
        email_hash = hash_email("shared@hotel.com")
        await make_guest(db, first_name="First", last_name="Guest", email_hash=email_hash)
        await make_guest(db, first_name="Second", last_name="Guest", email_hash=email_hash)
        await db.commit()

        repo = GuestRepository(db)
        found = await repo.get_by_email_hash(email_hash)
        # Should return the most-recently-created guest
        assert found is not None
        assert found.first_name == "Second"

    async def test_list_by_email_hash(self, db: AsyncSession):
        email_hash = hash_email("multi@hotel.com")
        await make_guest(db, first_name="A", last_name="Guest", email_hash=email_hash)
        await make_guest(db, first_name="B", last_name="Guest", email_hash=email_hash)
        await db.commit()

        repo = GuestRepository(db)
        results = await repo.list_by_email_hash(email_hash)
        assert len(results) == 2

    async def test_get_by_id(self, db: AsyncSession):
        guest = await make_guest(db, first_name="Target", last_name="User")
        await db.commit()

        repo = GuestRepository(db)
        found = await repo.get_by_id(guest.id)
        assert found is not None
        assert found.id == guest.id

    async def test_get_by_id_returns_none_for_unknown(self, db: AsyncSession):
        repo = GuestRepository(db)
        result = await repo.get_by_id(uuid.uuid4())
        assert result is None

    async def test_update_guest(self, db: AsyncSession):
        guest = await make_guest(db, first_name="Old", last_name="Name")
        await db.commit()

        repo = GuestRepository(db)
        updated = await repo.update(guest, first_name="New", nationality="GB")
        assert updated.first_name == "New"
        assert updated.nationality == "GB"

    async def test_preferences_stored_as_jsonb(self, db: AsyncSession):
        prefs = {"pillow": "soft", "floor": "high", "view": "ocean"}
        guest = await make_guest(db, preferences=prefs)
        await db.commit()

        repo = GuestRepository(db)
        found = await repo.get_by_id(guest.id)
        assert found.preferences == prefs


class TestPIIInReservationDetail:
    """Ensures PII is encrypted at rest but decrypted in API responses."""

    async def test_email_encrypted_in_db_decrypted_in_response(self, db: AsyncSession):
        from app.services.reservation_service import ReservationService
        from tests.conftest import FAKE_TENANT_ID, FAKE_TOKEN, FAKE_USER_ID
        from unittest.mock import AsyncMock, patch
        from app.core.ari_client import AvailabilityResult
        from app.schemas.reservation import ReservationCreate
        from app.schemas.guest import GuestCreate
        from decimal import Decimal

        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.check_availability = AsyncMock(
                return_value=AvailabilityResult(available=True, total_amount=Decimal("5000"), reason=None)
            )
            mock_ari.adjust_inventory = AsyncMock(return_value=True)

            svc = ReservationService(db)
            detail = await svc.create_reservation(
                ReservationCreate(
                    room_type_id=uuid.uuid4(),
                    rate_plan_id=uuid.uuid4(),
                    check_in=__import__("datetime").date(2026, 9, 1),
                    check_out=__import__("datetime").date(2026, 9, 3),
                    guest=GuestCreate(
                        first_name="Priya",
                        last_name="Sharma",
                        email="priya@hotel.com",
                        phone="+919800000000",
                    ),
                ),
                actor_id=FAKE_USER_ID,
                tenant_id=FAKE_TENANT_ID,
                token=FAKE_TOKEN,
            )

        # In the detail response, email should be decrypted plaintext
        assert detail.guest.email == "priya@hotel.com"
        assert detail.guest.phone == "+919800000000"

        # In the DB, the email field on GuestProfile should be bytes (encrypted)
        from app.repositories.guest_repo import GuestRepository

        repo = GuestRepository(db)
        db_guest = await repo.get_by_id(detail.guest.id)
        assert isinstance(db_guest.email, bytes)
        assert db_guest.email != b"priya@hotel.com"
        # But it decrypts correctly
        assert decrypt_pii(db_guest.email) == "priya@hotel.com"
