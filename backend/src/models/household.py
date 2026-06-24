from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateHouseholdRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class JoinHouseholdRequest(BaseModel):
    invite_code: str


class UserHouseholdResponse(BaseModel):
    id: UUID
    name: str
    invite_code: str
    role: str


class HouseholdMember(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    avatar_url: str | None


class HouseholdMembersResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    me: HouseholdMember
    others: list[HouseholdMember]
