from src.repository.repository import Repository
from src.errors import NotFoundException
from src.utils.logger import logger as log


class RecipeService:
    def __init__(self, db: Repository):
        self.db = db

    async def get_recipe_details(self, recipe_id: str, user_id: str | None = None) -> dict:
        """Get full recipe details. Includes user interactions if user_id provided."""
        recipe = await self.db.get_recipe_by_id(recipe_id)
        if not recipe:
            log.exception(f"Recipe {recipe_id} not found")
            raise NotFoundException("Recipe not found.")

        if user_id:
            interactions = await self.db.get_recipe_interactions(recipe_id, user_id)
            recipe.update(interactions)

        return recipe

    async def list_recipes(
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

        recipes, total = await self.db.find_recipes_with_count(
            search=search,
            recipe_type=recipe_type,
            labels=labels,
            ingredients=ingredients,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )

        if user_id and recipes:
            recipe_ids = [recipe["id"] for recipe in recipes]
            interactions_map = await self.db.get_recipes_interactions_bulk(recipe_ids, user_id)
            for recipe in recipes:
                recipe.update(interactions_map.get(recipe["id"], {}))

        return {
            "items": recipes,
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def toggle_recipe_like(self, recipe_id: str, user_id: str) -> bool:
        """Toggle like for a recipe. Returns True if now liked, False if unliked."""
        interacted = await self.db.has_interaction(recipe_id, user_id, "liked")
        if interacted:
            await self.db.remove_interaction(recipe_id, user_id, "liked")
            return False
        else:
            await self.db.add_interaction(recipe_id, user_id, "liked")
            return True

    async def toggle_recipe_cooked(self, recipe_id: str, user_id: str) -> bool:
        """Toggle cooked for a recipe. Returns True if now cooked, False if uncooked."""
        interacted = await self.db.has_interaction(recipe_id, user_id, "cooked")
        if interacted:
            await self.db.remove_interaction(recipe_id, user_id, "cooked")
            return False
        else:
            await self.db.add_interaction(recipe_id, user_id, "cooked")
            return True

    async def rate_recipe(self, recipe_id: str, user_id: str, rating: int) -> int:
        """Rate a recipe (1-5). The DB trigger keeps recipes.rating and num_ratings in sync."""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        await self.db.upsert_interaction(recipe_id, user_id, "rated", value=rating)
        return rating
