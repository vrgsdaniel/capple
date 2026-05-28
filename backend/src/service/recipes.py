from src.db.db import DB
from src.errors import NotFoundException
from src.utils.logger import logger as log


class RecipeService:
    def __init__(self, db: DB):
        self.db = db
        self._user_id = None
        self._liked_recipes = set()
        self._cooked_recipes = set()

    def set_context(self, context: dict | None):
        """Set execution context with user_id."""
        self._user_id = context.get("user_id") if context else None
        self._liked_recipes = set()
        self._cooked_recipes = set()
        if self._user_id:
            self._load_interactions()

    def _load_interactions(self):
        """Load all interactions for the user into memory."""
        interactions = self.db.get_all_user_interactions(self._user_id)
        self._liked_recipes = {r["recipe_id"] for r in interactions if r["interaction_type"] == "liked"}
        self._cooked_recipes = {r["recipe_id"] for r in interactions if r["interaction_type"] == "cooked"}

    def _ensure_user_id(self) -> str:
        """Get user_id from context. Raises if context not set."""
        if not self._user_id:
            raise ValueError("User context not available")
        return self._user_id

    def get_recipe_details(self, recipe_id: str) -> dict:
        """Get full recipe details. Includes user interactions if context is set."""
        recipe = self.db.get_recipe_by_id(recipe_id)
        if not recipe:
            log.exception(f"Recipe {recipe_id} not found")
            raise NotFoundException("Recipe not found.")

        if self._user_id:
            recipe["liked"] = recipe_id in self._liked_recipes
            recipe["cooked"] = recipe_id in self._cooked_recipes

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
        """List recipes with filtering, sorting, and pagination. Includes user interactions if context is set."""
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

        # Enrich with user interactions if context available (from pre-loaded sets)
        if self._user_id:
            for recipe in recipes:
                recipe["liked"] = recipe["id"] in self._liked_recipes
                recipe["cooked"] = recipe["id"] in self._cooked_recipes

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

    def toggle_recipe_like(self, recipe_id: str) -> bool:
        """Toggle like for a recipe. Returns True if now liked, False if unliked. Requires context."""
        user_id = self._ensure_user_id()

        interacted = self.db.has_interaction(recipe_id, user_id, "liked")
        if interacted:
            self.db.remove_interaction(recipe_id, user_id, "liked")
            self._liked_recipes.discard(recipe_id)
            return False
        else:
            self.db.add_interaction(recipe_id, user_id, "liked")
            self._liked_recipes.add(recipe_id)
            return True

    def toggle_recipe_cooked(self, recipe_id: str) -> bool:
        """Toggle cooked for a recipe. Returns True if now cooked, False if uncooked. Requires context."""
        user_id = self._ensure_user_id()

        interacted = self.db.has_interaction(recipe_id, user_id, "cooked")
        if interacted:
            self.db.remove_interaction(recipe_id, user_id, "cooked")
            self._cooked_recipes.discard(recipe_id)
            return False
        else:
            self.db.add_interaction(recipe_id, user_id, "cooked")
            self._cooked_recipes.add(recipe_id)
            return True
