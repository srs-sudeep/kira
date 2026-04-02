---
sidebar_position: 1
---

# Identity Service

The authentication and authorization hub for the KIRA platform. Runs on port **8001**.

## Responsibilities

- User registration, login, and session management
- JWT access token and refresh token issuance
- RBAC role assignment and permission enforcement
- TOTP-based MFA with backup codes
- Immutable audit log
- Tenant context for multi-tenancy

## Key Endpoints

### Authentication

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login, returns access + refresh tokens |
| `POST` | `/auth/refresh` | Refresh access token |
| `POST` | `/auth/logout` | Revoke refresh token |
| `GET` | `/auth/me` | Get current user profile |
| `PATCH` | `/auth/me` | Update current user profile |
| `POST` | `/auth/change-password` | Change password |

### MFA

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/mfa/setup` | Generate TOTP secret + QR code |
| `POST` | `/auth/mfa/verify` | Enable MFA (confirm 6-digit code) |
| `POST` | `/auth/mfa/disable` | Disable MFA |
| `GET` | `/auth/mfa/backup-codes` | Get backup codes |

### Users (hotel_admin+ only)

| Method | Path | Description |
|---|---|---|
| `GET` | `/users/` | List users in tenant |
| `POST` | `/users/invite` | Invite user by email |
| `PATCH` | `/users/{user_id}` | Update user role |
| `POST` | `/users/{user_id}/deactivate` | Deactivate user |
| `POST` | `/users/{user_id}/reactivate` | Reactivate user |

### Audit Log

| Method | Path | Description |
|---|---|---|
| `GET` | `/audit-log/` | Paginated audit entries (filters: action, user, date range) |

## Data Models

### User

```python
class User(Base):
    id: UUID
    tenant_id: UUID           # null for super_admin
    email: str                # unique in public schema
    full_name: str
    hashed_password: str
    role: UserRole            # super_admin | hotel_admin | manager | front_desk
    is_active: bool
    mfa_enabled: bool
    mfa_secret: str | None    # encrypted TOTP secret
    avatar_url: str | None
    created_at: datetime
    last_login_at: datetime | None
```

### AuditLog

```python
class AuditLog(Base):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    action: str               # e.g., "rate_plan.update"
    resource_type: str        # e.g., "RatePlan"
    resource_id: str | None
    ip_address: str
    user_agent: str | None
    details: dict             # JSONB
    created_at: datetime
```

## Configuration

```python
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str           # 32-char, for cookie signing
    JWT_SECRET_KEY: str       # 64-char, for JWT signing
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str            # for token blacklist
```

## Token Revocation

Revoked tokens are tracked in Redis with TTL equal to the token's remaining lifetime. On each request, the Kong JWT plugin validates the signature; the service checks the Redis blacklist for revoked tokens.
