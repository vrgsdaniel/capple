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

    async def list_recipes(self, user_id: str, search_spec: dict) -> dict:
        """Search recipes while keeping changeable filtering and ranking rules in the service."""
        recipes = await self.db.find_recipe_candidates(search_spec.get("text"))
        interactions = await self.db.get_recipes_interactions_bulk(
            [str(recipe["id"]) for recipe in recipes],
            user_id,
        )

        enriched = [
            self._normalize_recipe(
                recipe,
                interactions.get(
                    str(recipe["id"]),
                    {"liked": False, "cooked": False, "user_rating": None},
                ),
            )
            for recipe in recipes
        ]
        filtered = [recipe for recipe in enriched if self._matches_filters(recipe, search_spec)]
        sort = search_spec.get("sort", "relevance")
        if not search_spec.get("text") and sort == "relevance":
            sort = "highest_rated"
        filtered.sort(key=lambda recipe: self._sort_key(recipe, sort))

        page = search_spec.get("page", 1)
        limit = search_spec.get("limit", 24)
        offset = (page - 1) * limit
        items = filtered[offset : offset + limit]

        return {
            "items": items,
            "total": len(filtered),
            "page": page,
            "limit": limit,
        }

    @staticmethod
    def _normalize_recipe(recipe: dict, interactions: dict) -> dict:
        return {
            **recipe,
            "recipe_type": recipe.get("recipe_type") or "",
            "labels": recipe.get("labels") or [],
            "ingredients": recipe.get("ingredients") or [],
            "prep_time_minutes": recipe.get("prep_time_minutes") or 0,
            "cook_time_minutes": recipe.get("cook_time_minutes") or 0,
            "image_uri": recipe.get("image_uri") or "",
            "num_ratings": recipe.get("num_ratings") or 0,
            "relevance": recipe.get("relevance") or 0.0,
            **interactions,
        }

    @classmethod
    def _matches_filters(cls, recipe: dict, search_spec: dict) -> bool:
        meal_types = set(search_spec.get("meal_types") or [])
        if meal_types and str(recipe["recipe_type"]).lower() not in meal_types:
            return False

        labels = set(search_spec.get("labels") or [])
        recipe_labels = {str(label).lower() for label in recipe["labels"]}
        if labels and recipe_labels.isdisjoint(labels):
            return False

        ingredients = search_spec.get("ingredients") or []
        ingredient_text = " ".join(cls._ingredient_text(value) for value in recipe["ingredients"]).lower()
        if ingredients and not any(ingredient in ingredient_text for ingredient in ingredients):
            return False

        max_total_minutes = search_spec.get("max_total_minutes")
        total_minutes = recipe["prep_time_minutes"] + recipe["cook_time_minutes"]
        if max_total_minutes is not None and total_minutes > max_total_minutes:
            return False

        for interaction_type in ("liked", "cooked"):
            expected = search_spec.get(interaction_type)
            if expected is not None and recipe[interaction_type] is not expected:
                return False
        return True

    @staticmethod
    def _ingredient_text(value: object) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for key in ("name", "item", "label"):
                if value.get(key):
                    return str(value[key])
        return str(value)

    @staticmethod
    def _sort_key(recipe: dict, sort: str) -> tuple:
        name = str(recipe.get("name") or "").lower()
        recipe_id = str(recipe["id"])
        rating = recipe.get("rating")
        rating_key = (rating is None, -float(rating or 0))

        if sort == "fastest":
            return (
                recipe["prep_time_minutes"] + recipe["cook_time_minutes"],
                name,
                recipe_id,
            )
        if sort == "name":
            return (name, recipe_id)
        if sort == "relevance":
            return (-float(recipe["relevance"]), *rating_key, name, recipe_id)
        return (*rating_key, name, recipe_id)

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
