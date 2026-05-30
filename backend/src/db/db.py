from supabase import create_client, Client
from src.settings import get_supabase_settings
from src.db.criteria import Criteria
from src.db.store import Store
from src.utils.logger import logger as log


class DB:
    _APP_SCHEMA = "app"

    def __init__(self):
        settings = get_supabase_settings()
        self.client: Client = create_client(settings.url, settings.service_role_key)

    def store(self, table_name: str) -> Store:
        """Return a :class:`Store` bound to *table_name*."""
        return Store(self.client, table_name, schema_name=self._APP_SCHEMA)

    def is_alive(self) -> bool:
        try:
            self.store("profiles").find_one(Criteria().select("id"))
            return True
        except Exception:
            log.exception("Database connection failed")
            return False

    # --- profiles ---

    def get_profile_by_id(self, user_id: str) -> dict | None:
        return self.store("profiles").get_by_id(user_id)

    # --- households ---

    def create_household(self, name: str, created_by: str) -> dict:
        return self.store("households").insert({"name": name, "created_by": created_by})

    def get_household_by_code(self, invite_code: str) -> dict | None:
        return self.store("households").find_one(Criteria().eq("invite_code", invite_code))

    def get_household_by_user(self, user_id: str) -> dict | None:
        membership = self.store("household_members").find_one(Criteria().eq("user_id", user_id))
        if not membership:
            return None
        household = self.store("households").get_by_id(membership["household_id"])
        if not household:
            return None
        return {**household, "role": membership["role"]}

    def add_member_to_household(self, household_id: str, user_id: str, role: str = "member") -> dict:
        return self.store("household_members").insert({"household_id": household_id, "user_id": user_id, "role": role})

    # --- battery_logs ---

    def create_battery_log(
        self, user_id: str, household_id: str, level: int, note: str | None, effective_at: str
    ) -> dict:
        return self.store("battery_logs").insert(
            {
                "user_id": user_id,
                "household_id": household_id,
                "level": level,
                "note": note,
                "effective_at": effective_at,
            }
        )

    def update_battery_log(self, log_id: str, user_id: str, data: dict) -> dict | None:
        result = self.store("battery_logs").update_where(
            Criteria().eq("id", log_id).eq("user_id", user_id),
            data,
        )
        return result[0] if result else None

    def delete_battery_log(self, log_id: str, user_id: str) -> bool:
        result = self.store("battery_logs").delete_where(Criteria().eq("id", log_id).eq("user_id", user_id))
        return len(result) > 0

    def find_battery_logs_by_household(self, household_id: str, start: str, end: str) -> list[dict]:
        return self.store("battery_logs").find(
            Criteria()
            .eq("household_id", household_id)
            .gte("effective_at", start)
            .lte("effective_at", end)
            .order("effective_at", ascending=False)
        )

    # --- recipes ---

    def get_recipe_by_id(self, recipe_id: str) -> dict | None:
        """Get full recipe details row."""
        return self.store("recipes").find_one(Criteria().eq("id", recipe_id))

    def find_recipes(
        self,
        search: str | None = None,
        recipe_type: str | None = None,
        labels: list[str] | None = None,
        ingredients: list[str] | None = None,
        sort_by: str = "cook_time_minutes",
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 20,
    ) -> list[dict]:
        """Find recipes with filtering and pagination."""
        criteria = Criteria()

        # Search filter (ILIKE on name)
        if search:
            # TODO: For better search, consider adding a tsvector column and using full-text search instead of ILIKE
            criteria = criteria.ilike("name", f"%{search}%")

        # Exact filters
        if recipe_type:
            criteria = criteria.eq("recipe_type", recipe_type)

        # Sorting (validate to prevent injection)
        valid_sorts = {"rating", "prep_time_minutes", "cook_time_minutes"}
        sort_col = sort_by if sort_by in valid_sorts else "cook_time_minutes"
        sort_asc = sort_order.lower() != "desc"
        criteria = criteria.order(sort_col, ascending=sort_asc)

        # Pagination
        offset = (page - 1) * limit
        criteria = criteria.limit(limit).offset(offset)

        recipes = self.store("recipes").find(criteria)

        # Filter by labels/ingredients (client-side for simplicity, can be optimized later)
        if labels or ingredients:
            recipes = self._filter_recipes_by_arrays(recipes, labels, ingredients)

        return recipes

    def count_recipes(
        self,
        search: str | None = None,
        recipe_type: str | None = None,
        labels: list[str] | None = None,
        ingredients: list[str] | None = None,
    ) -> int:
        """Count total recipes matching criteria."""
        criteria = Criteria()

        if search:
            # TODO: For better search, consider adding a tsvector column and using full-text search instead of ILIKE
            criteria = criteria.ilike("name", f"%{search}%")
        if recipe_type:
            criteria = criteria.eq("recipe_type", recipe_type)

        total = self.store("recipes").count(criteria)

        # If we're filtering by labels/ingredients, adjust count
        if labels or ingredients:
            # For accurate count, we'd need to fetch all matching recipes and filter
            # For MVP, we return the unfiltered count (slight inaccuracy acceptable)
            pass

        return total

    def _filter_recipes_by_arrays(
        self, recipes: list[dict], labels: list[str] | None, ingredients: list[str] | None
    ) -> list[dict]:
        """Filter recipes by labels or ingredients (client-side JSONB filtering)."""
        filtered = recipes
        if labels:
            label_set = set(labels)
            filtered = [r for r in filtered if r.get("labels") and any(label in label_set for label in r["labels"])]
        if ingredients:
            ingredient_set = set(ingredients)
            filtered = [
                r for r in filtered if r.get("ingredients") and any(ing in ingredient_set for ing in r["ingredients"])
            ]
        return filtered

    # --- recipe user interactions ---

    def get_recipe_interactions(self, recipe_id: str, user_id: str) -> dict:
        """Get all interactions for a specific recipe and user. Returns dict with liked, cooked, user_rating."""
        interactions = self.store("recipe_user_interactions").find(
            Criteria().eq("user_id", user_id).eq("recipe_id", recipe_id)
        )
        result = {"liked": False, "cooked": False, "user_rating": None}
        for interaction in interactions:
            if interaction["interaction_type"] == "liked":
                result["liked"] = True
            elif interaction["interaction_type"] == "cooked":
                result["cooked"] = True
            elif interaction["interaction_type"] == "rated":
                result["user_rating"] = interaction.get("value")
        return result

    def get_recipes_interactions_bulk(self, recipe_ids: list[str], user_id: str) -> dict[str, dict]:
        """Get interactions for multiple recipes. Returns dict mapping recipe_id -> {liked, cooked, user_rating}."""
        if not recipe_ids:
            return {}

        interactions = self.store("recipe_user_interactions").find(
            Criteria().eq("user_id", user_id).in_("recipe_id", recipe_ids)
        )

        # Initialize all recipes with no interactions
        result = {recipe_id: {"liked": False, "cooked": False, "user_rating": None} for recipe_id in recipe_ids}

        # Populate with actual interactions
        for interaction in interactions:
            recipe_id = interaction["recipe_id"]
            if interaction["interaction_type"] == "liked":
                result[recipe_id]["liked"] = True
            elif interaction["interaction_type"] == "cooked":
                result[recipe_id]["cooked"] = True
            elif interaction["interaction_type"] == "rated":
                result[recipe_id]["user_rating"] = interaction.get("value")

        return result

    def has_interaction(self, recipe_id: str, user_id: str, interaction_type: str) -> bool:
        """Check if user has an interaction for recipe."""
        result = self.store("recipe_user_interactions").find_one(
            Criteria().eq("user_id", user_id).eq("recipe_id", recipe_id).eq("interaction_type", interaction_type)
        )
        return result is not None

    def add_interaction(self, recipe_id: str, user_id: str, interaction_type: str, value: int | None = None) -> dict:
        """Add a user recipe interaction (like, cooked, rated)."""
        return self.store("recipe_user_interactions").insert(
            {
                "recipe_id": recipe_id,
                "user_id": user_id,
                "interaction_type": interaction_type,
                "value": value,
            }
        )

    def upsert_interaction(
        self, recipe_id: str, user_id: str, interaction_type: str, value: int | None = None
    ) -> dict:
        """Insert or update a user recipe interaction in a single DB call."""
        return self.store("recipe_user_interactions").upsert(
            {
                "recipe_id": recipe_id,
                "user_id": user_id,
                "interaction_type": interaction_type,
                "value": value,
            },
            on_conflict="user_id,recipe_id,interaction_type",
        )

    def remove_interaction(self, recipe_id: str, user_id: str, interaction_type: str) -> bool:
        """Remove a user recipe interaction."""
        criteria = (
            Criteria().eq("user_id", user_id).eq("recipe_id", recipe_id).eq("interaction_type", interaction_type)
        )

        result = self.store("recipe_user_interactions").delete_where(criteria)
        return len(result) > 0


def get_db() -> DB:
    """Factory function for DB to allow dependency injection."""
    return DB()
