from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AddGroceryItemRequest(BaseModel):
    name: str = Field(..., min_length=1)
    qty: str | None = None


class AddFromRecipeRequest(BaseModel):
    recipe_id: str
    ingredients: list[dict]


class PatchGroceryItemRequest(BaseModel):
    bought: bool


class GroceryItemResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    household_id: UUID
    name: str
    qty: str | None = None
    bought: bool
    bought_at: datetime | None = None
    source_recipe_title: str | None = None
    added_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class GroceryListResponse(BaseModel):
    active: list[GroceryItemResponse]
    history: list[GroceryItemResponse]
