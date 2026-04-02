"""Pydantic v2 schemas for seasonal rules."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AdjustmentType = Literal["percentage", "fixed"]


class SeasonalRuleCreate(BaseModel):
    room_type_id: uuid.UUID | None = None  # None = all room types
    rate_plan_id: uuid.UUID | None = None  # None = all rate plans
    name: str = Field(min_length=1, max_length=255)
    start_date: date
    end_date: date
    adjustment_type: AdjustmentType
    adjustment_value: Decimal = Field(decimal_places=2)

    @model_validator(mode="after")
    def valid_dates(self) -> "SeasonalRuleCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date.")
        return self


class SeasonalRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    adjustment_type: AdjustmentType | None = None
    adjustment_value: Decimal | None = Field(default=None, decimal_places=2)
    is_active: bool | None = None


class SeasonalRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    room_type_id: uuid.UUID | None
    rate_plan_id: uuid.UUID | None
    name: str
    start_date: date
    end_date: date
    adjustment_type: str
    adjustment_value: Decimal
    is_active: bool
    created_at: datetime


class SeasonalRuleListResponse(BaseModel):
    items: list[SeasonalRuleResponse]
    total: int
