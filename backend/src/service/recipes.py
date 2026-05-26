from src.db.db import DB
from src.errors import NotFoundException
from src.utils.logger import logger as log


class RecipeService:
    def __init__(self, db: DB):
        self.db = db

    def get_recipe_details(self, recipe_id: str) -> dict:
        """Get full recipe details."""
        recipe = self.db.get_recipe_by_id(recipe_id)
        if not recipe:
            log.exception(f"Recipe {recipe_id} not found")
            raise NotFoundException("Recipe not found.")
        return recipe

    def list_recipes(
        self,
        search: str | None = None,
        recipe_type: str | None = None,
        labels: list[str] | None = None,
        ingredients: list[str] | None = None,
        sort_by: str = "cook_time_minutes",
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """List recipes with filtering, sorting, and pagination."""
        # Validate pagination params
        page = max(1, page)
        limit = min(100, max(1, limit))  # Cap at 100 items per page

        # Fetch recipes
        recipes = self.db.find_recipes(
            search=search,
            recipe_type=recipe_type,
            labels=labels,
            ingredients=ingredients,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )

        # Get total count
        total = self.db.count_recipes(
            search=search,
            recipe_type=recipe_type,
            labels=labels,
            ingredients=ingredients,
        )

        return {
            "items": recipes,
            "total": total,
            "page": page,
            "limit": limit,
        }
