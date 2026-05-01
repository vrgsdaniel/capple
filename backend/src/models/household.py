from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel


class Household(BaseModel):
    id: UUID = uuid4()
    name: str
    invite_code: str = str(uuid4())[:8]
    created_at: datetime = datetime.now()


class CreateHouseholdRequest(BaseModel):
    name: str


class JoinHouseholdRequest(BaseModel):
    invite_code: str
