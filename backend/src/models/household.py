from uuid import UUID

from pydantic import BaseModel


class CreateHouseholdRequest(BaseModel):
    name: str


class JoinHouseholdRequest(BaseModel):
    invite_code: str


class UserHouseholdResponse(BaseModel):
    id: UUID
    name: str
    invite_code: str
    role: str
