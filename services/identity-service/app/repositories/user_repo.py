"""Repository for public.users and public.refresh_tokens."""
import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── User queries ──────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._s.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._s.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self, tenant_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[User], int]:
        offset = (page - 1) * page_size
        base = select(User).where(User.tenant_id == tenant_id, User.is_active.is_(True))
        total = (
            await self._s.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._s.execute(
                base.order_by(User.created_at.desc()).offset(offset).limit(page_size)
            )
        ).scalars().all()
        return list(rows), total

    async def create(
        self,
        *,
        email: str,
        hashed_password: str,
        first_name: str,
        last_name: str,
        role: str,
        tenant_id: uuid.UUID | None,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            tenant_id=tenant_id,
        )
        self._s.add(user)
        await self._s.flush()
        await self._s.refresh(user)
        return user

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            setattr(user, key, value)
        await self._s.flush()
        await self._s.refresh(user)
        return user

    async def soft_delete(self, user: User) -> None:
        user.is_active = False
        await self._s.flush()

    # ── Brute-force helpers ───────────────────────────────────────────────────

    async def increment_failed_attempts(self, user: User) -> None:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        await self._s.flush()

    async def reset_failed_attempts(self, user: User) -> None:
        user.failed_login_attempts = 0
        user.locked_until = None
        await self._s.flush()

    async def lock_until(self, user: User, until: datetime) -> None:
        user.locked_until = until
        await self._s.flush()

    # ── Refresh token queries ─────────────────────────────────────────────────

    async def create_refresh_token(
        self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self._s.add(rt)
        await self._s.flush()
        return rt

    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._s.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, rt: RefreshToken) -> None:
        rt.revoked = True
        await self._s.flush()

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        await self._s.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
        await self._s.flush()
