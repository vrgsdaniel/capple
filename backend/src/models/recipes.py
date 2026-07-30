from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecipeMealType(StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class RecipeSort(StrEnum):
    RELEVANCE = "relevance"
    FASTEST = "fastest"
    HIGHEST_RATED = "highest_rated"
    NAME = "name"


class RecipeSearchSpec(BaseModel):
    """Validated, deterministic recipe search input."""

    text: str | None = Field(default=None, max_length=200)
    meal_types: list[RecipeMealType] = Field(default_factory=list, max_length=10)
    labels: list[str] = Field(default_factory=list, max_length=20)
    ingredients: list[str] = Field(default_factory=list, max_length=20)
    max_total_minutes: int | None = Field(default=None, ge=1, le=1440)
    liked: bool | None = None
    cooked: bool | None = None
    sort: RecipeSort = "relevance"
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=24, ge=1, le=100)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        normalized = value.strip() if value else ""
        return normalized or None

    @field_validator("labels", "ingredients")
    @classmethod
    def normalize_terms(cls, values: list[str]) -> list[str]:
        normalized = [value.strip().lower() for value in values if value.strip()]
        return list(dict.fromkeys(normalized))


class RateRecipeRequest(BaseModel):
    """Request to rate a recipe."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")


class RecipeDetailsResponse(BaseModel):
    """Full recipe details (everything except created_at)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    labels: list
    ingredients: list
    instructions: str
    recipe_type: str
    prep_time_minutes: int
    cook_time_minutes: int
    source_name: str = ""
    source_url: str = ""
    servings: int | None = None
    rating: float | None = None
    image_uri: str = ""
    liked: bool = False
    cooked: bool = False
    user_rating: int | None = None
    num_ratings: int = 0


class RecipeListItemResponse(BaseModel):
    """Recipe summary for list endpoint."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    recipe_type: str
    labels: list
    prep_time_minutes: int
    cook_time_minutes: int
    rating: float | None = None
    image_uri: str = ""
    liked: bool = False
    cooked: bool = False
    user_rating: int | None = None
    num_ratings: int = 0


class RecipeListResponse(BaseModel):
    """Paginated list of recipes."""

    model_config = ConfigDict(extra="ignore")

    items: list[RecipeListItemResponse]
    total: int
    page: int
    limit: int
