"""Pydantic v2 schemas for tenant management."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SubscriptionTier = Literal["free", "starter", "professional", "enterprise"]


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str = "IND"
    postal_code: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    star_rating: int | None = Field(None, ge=1, le=5)
    base_currency: str = "INR"
    timezone: str = "Asia/Kolkata"
    logo_url: str | None = None
    subscription_tier: SubscriptionTier = "starter"


class TenantMeUpdate(BaseModel):
    """Fields a property_owner can update on their own tenant."""
    name: str | None = Field(None, min_length=1, max_length=255)
    legal_name: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    star_rating: int | None = Field(None, ge=1, le=5)
    base_currency: str | None = None
    timezone: str | None = None
    logo_url: str | None = None


class TenantAdminUpdate(BaseModel):
    """Fields a super_admin can update on any tenant."""
    name: str | None = Field(None, min_length=1, max_length=255)
    subscription_tier: SubscriptionTier | None = None
    is_active: bool | None = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    legal_name: str | None
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    country: str
    postal_code: str | None
    phone: str | None
    email: str | None
    website: str | None
    star_rating: int | None
    base_currency: str
    timezone: str
    logo_url: str | None
    subscription_tier: str
    schema_name: str
    is_active: bool
    onboarded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
    page: int
    page_size: int
    pages: int
