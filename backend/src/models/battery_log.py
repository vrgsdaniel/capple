from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateBatteryLogRequest(BaseModel):
    level: int = Field(..., ge=0, le=100)
    note: str | None = Field(None, max_length=500)
    effective_at: datetime


class UpdateBatteryLogRequest(BaseModel):
    level: int | None = Field(None, ge=0, le=100)
    note: str | None = Field(None, max_length=500)
    effective_at: datetime | None = None


class BatteryLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    household_id: UUID
    level: int
    note: str | None
    effective_at: datetime
    logged_at: datetime


class BatteryLogsQueryParams(BaseModel):
    start: datetime
    end: datetime
