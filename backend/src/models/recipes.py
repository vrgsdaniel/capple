from pydantic import BaseModel, ConfigDict


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
    rating: int | None = None
    image_uri: str = ""
    liked: bool = False
    cooked: bool = False


class RecipeListItemResponse(BaseModel):
    """Recipe summary for list endpoint."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    recipe_type: str
    labels: list
    prep_time_minutes: int
    cook_time_minutes: int
    rating: int | None = None
    image_uri: str = ""
    liked: bool = False
    cooked: bool = False


class RecipeListResponse(BaseModel):
    """Paginated list of recipes."""

    model_config = ConfigDict(extra="ignore")

    items: list[RecipeListItemResponse]
    total: int
    page: int
    limit: int
