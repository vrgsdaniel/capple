from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AddGroceryItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    qty: str | None = None


class AddFromRecipeIngredientRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    qty: str | None = None


class AddFromRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: str = Field(..., min_length=1)
    ingredients: list[AddFromRecipeIngredientRequest]


class PatchGroceryItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
