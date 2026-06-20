from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

AssigneeType = Literal["none", "specific", "all"]
Frequency = Literal["daily", "weekly", "monthly"]


class CreateTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    assignee_type: AssigneeType = "none"
    assignee_id: UUID | None = None
    due_date: date | None = None
    frequency: Frequency | None = None

    @model_validator(mode="after")
    def validate_assignee(self) -> "CreateTaskRequest":
        if self.assignee_type == "specific" and self.assignee_id is None:
            raise ValueError("assignee_id is required when assignee_type is 'specific'")
        if self.assignee_type != "specific" and self.assignee_id is not None:
            raise ValueError("assignee_id must be null when assignee_type is not 'specific'")
        return self


class UpdateTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1)
    assignee_type: AssigneeType | None = None
    assignee_id: UUID | None = None
    due_date: date | None = None
    frequency: Frequency | None = None

    @model_validator(mode="after")
    def validate_assignee(self) -> "UpdateTaskRequest":
        if self.assignee_type == "specific" and self.assignee_id is None:
            raise ValueError("assignee_id is required when assignee_type is 'specific'")
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    household_id: UUID
    name: str
    assignee_type: str
    assignee_id: UUID | None = None
    due_date: date | None = None
    frequency: str | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class TaskListResponse(BaseModel):
    active: list[TaskResponse]
    history: list[TaskResponse]
    active_total: int
    history_total: int
    page: int
    page_size: int
