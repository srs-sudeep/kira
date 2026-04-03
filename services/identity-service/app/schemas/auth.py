"""Pydantic v2 schemas for authentication flows."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.email_types import LooseEmailStr
from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    email: LooseEmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    # None for super_admin bootstrapping; required for all other roles
    tenant_id: uuid.UUID | None = None


class LoginRequest(BaseModel):
    email: LooseEmailStr
    password: str
    # Supplied on the second step when the account has MFA enabled
    totp_code: str | None = None


class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access_token expiry
    user_id: uuid.UUID
    role: str
    mfa_required: bool = False
    # Populated on full login; omitted when MFA step is required
    user: UserResponse | None = None
    # MFA pending JWT — client sends as Bearer on POST /auth/login/mfa
    mfa_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MfaSetupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    secret: str
    provisioning_uri: str
    qr_code_base64: str  # PNG encoded as base64 for direct use in <img src="data:...">


class MfaVerifyRequest(BaseModel):
    totp_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
