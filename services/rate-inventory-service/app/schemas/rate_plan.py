"""Pydantic v2 schemas for rate plans."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PlanType = Literal["bar", "non_refundable", "corporate", "package", "promotional"]
DerivedType = Literal["fixed", "percentage"]


class RatePlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    plan_type: PlanType
    base_amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field("INR", min_length=3, max_length=3)
    cancellation_policy: dict[str, Any] | None = None
    deposit_policy: dict[str, Any] | None = None
    derived_from_id: uuid.UUID | None = None
    derived_type: DerivedType | None = None
    derived_value: Decimal | None = None
    min_los: int = Field(1, ge=1)
    max_los: int = Field(365, ge=1)

    @model_validator(mode="after")
    def check_derived_fields(self) -> "RatePlanCreate":
        has_parent = self.derived_from_id is not None
        has_type = self.derived_type is not None
        has_value = self.derived_value is not None
        if has_parent and not (has_type and has_value):
            raise ValueError("derived_type and derived_value are required when derived_from_id is set.")
        if not has_parent and (has_type or has_value):
            raise ValueError("derived_type/derived_value only apply when derived_from_id is set.")
        return self


class RatePlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    plan_type: PlanType | None = None
    base_amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    cancellation_policy: dict[str, Any] | None = None
    deposit_policy: dict[str, Any] | None = None
    derived_type: DerivedType | None = None
    derived_value: Decimal | None = None
    min_los: int | None = Field(default=None, ge=1)
    max_los: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class RatePlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_type_id: uuid.UUID
    name: str
    plan_type: str
    base_amount: Decimal
    currency: str
    cancellation_policy: dict[str, Any] | None
    deposit_policy: dict[str, Any] | None
    derived_from_id: uuid.UUID | None
    derived_type: str | None
    derived_value: Decimal | None
    min_los: int
    max_los: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RatePlanListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[RatePlanResponse]
    total: int
