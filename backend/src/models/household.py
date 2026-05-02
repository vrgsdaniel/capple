from uuid import UUID

from pydantic import BaseModel, Field


class CreateHouseholdRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class JoinHouseholdRequest(BaseModel):
    invite_code: str


class UserHouseholdResponse(BaseModel):
    id: UUID
    name: str
    invite_code: str
    role: str
