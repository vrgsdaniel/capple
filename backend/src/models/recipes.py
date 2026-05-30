from pydantic import BaseModel, ConfigDict, Field


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
