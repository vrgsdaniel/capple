from src.db.db import DB
from src.errors import NotFoundException
from src.utils.logger import logger as log


class RecipeService:
    def __init__(self, db: DB):
        self.db = db

    def get_recipe_details(self, recipe_id: str, user_id: str | None = None) -> dict:
        """Get full recipe details. Includes user interactions if user_id provided."""
        recipe = self.db.get_recipe_by_id(recipe_id)
        if not recipe:
            log.exception(f"Recipe {recipe_id} not found")
            raise NotFoundException("Recipe not found.")

        if user_id:
            interactions = self.db.get_recipe_interactions(recipe_id, user_id)
            recipe.update(interactions)

        return recipe

    def list_recipes(
        self,
        user_id: str | None = None,
        search: str | None = None,
        recipe_type: str | None = None,
        labels: list[str] | None = None,
        ingredients: list[str] | None = None,
        sort_by: str = "cook_time_minutes",
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """List recipes with filtering, sorting, and pagination. Includes user interactions if user_id provided."""
        # Validate pagination params
        page = max(1, page)
        limit = min(100, max(1, limit))

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

        # Enrich with user interactions if user_id provided
        if user_id and recipes:
            recipe_ids = [recipe["id"] for recipe in recipes]
            interactions_map = self.db.get_recipes_interactions_bulk(recipe_ids, user_id)
            for recipe in recipes:
                recipe.update(interactions_map.get(recipe["id"], {}))

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

    def toggle_recipe_like(self, recipe_id: str, user_id: str) -> bool:
        """Toggle like for a recipe. Returns True if now liked, False if unliked."""
        interacted = self.db.has_interaction(recipe_id, user_id, "liked")
        if interacted:
            self.db.remove_interaction(recipe_id, user_id, "liked")
            return False
        else:
            self.db.add_interaction(recipe_id, user_id, "liked")
            return True

    def toggle_recipe_cooked(self, recipe_id: str, user_id: str) -> bool:
        """Toggle cooked for a recipe. Returns True if now cooked, False if uncooked."""
        interacted = self.db.has_interaction(recipe_id, user_id, "cooked")
        if interacted:
            self.db.remove_interaction(recipe_id, user_id, "cooked")
            return False
        else:
            self.db.add_interaction(recipe_id, user_id, "cooked")
            return True

    def rate_recipe(self, recipe_id: str, user_id: str, rating: int) -> int:
        """Rate a recipe (1-5). The DB trigger keeps recipes.rating and num_ratings in sync."""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        self.db.upsert_interaction(recipe_id, user_id, "rated", value=rating)
        return rating
