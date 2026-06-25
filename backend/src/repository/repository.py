import re

from fastapi import Request
from supabase import AsyncClient

from src.repository.criteria import Criteria
from src.repository.store import Store
from src.utils.general import timestamp
from src.utils.logger import logger as log


class Repository:
    _APP_SCHEMA = "app"

    def __init__(self, client: AsyncClient):
        self.client = client

    def store(self, table_name: str) -> Store:
        """Return a :class:`Store` bound to *table_name*."""
        return Store(self.client, table_name, schema_name=self._APP_SCHEMA)

    @staticmethod
    def _normalize_grocery_name(name: str) -> str:
        return re.sub(r"\s+", " ", str(name or "").lower().strip())

    async def is_alive(self) -> bool:
        try:
            await self.store("profiles").find_one(Criteria().select("id"))
            return True
        except Exception:
            log.exception("Database connection failed")
            return False

    # --- profiles ---

    async def get_profile_by_id(self, user_id: str) -> dict | None:
        return await self.store("profiles").get_by_id(user_id)

    # --- households ---

    async def create_household(self, name: str, created_by: str) -> dict:
        return await self.store("households").insert({"name": name, "created_by": created_by})

    async def get_household_by_code(self, invite_code: str) -> dict | None:
        return await self.store("households").find_one(Criteria().eq("invite_code", invite_code))

    async def get_household_by_user(self, user_id: str) -> dict | None:
        membership = await self.store("household_members").find_one(Criteria().eq("user_id", user_id))
        if not membership:
            return None
        household = await self.store("households").get_by_id(membership["household_id"])
        if not household:
            return None
        return {**household, "role": membership["role"]}

    async def add_member_to_household(self, household_id: str, user_id: str, role: str = "member") -> dict:
        return await self.store("household_members").insert(
            {"household_id": household_id, "user_id": user_id, "role": role}
        )

    async def get_household_members(self, user_id: str) -> list[dict]:
        return await self.store("household_member_profiles").find(
            Criteria()
            .eq("request_user_id", user_id)
            .order("created_at", ascending=True)
            .select("id, display_name, avatar_url")
        )

    # --- battery_logs ---

    async def create_battery_log(
        self, user_id: str, household_id: str, level: int, note: str | None, effective_at: str
    ) -> dict:
        return await self.store("battery_logs").insert(
            {
                "user_id": user_id,
                "household_id": household_id,
                "level": level,
                "note": note,
                "effective_at": effective_at,
            }
        )

    async def update_battery_log(self, log_id: str, user_id: str, data: dict) -> dict | None:
        result = await self.store("battery_logs").update_where(
            Criteria().eq("id", log_id).eq("user_id", user_id),
            data,
        )
        return result[0] if result else None

    async def delete_battery_log(self, log_id: str, user_id: str) -> bool:
        result = await self.store("battery_logs").delete_where(Criteria().eq("id", log_id).eq("user_id", user_id))
        return len(result) > 0

    async def find_battery_logs_by_household(self, household_id: str, start: str, end: str) -> list[dict]:
        return await self.store("battery_logs").find(
            Criteria()
            .eq("household_id", household_id)
            .gte("effective_at", start)
            .lte("effective_at", end)
            .order("effective_at", ascending=False)
        )

    # --- recipes ---

    async def get_recipe_by_id(self, recipe_id: str) -> dict | None:
        """Get full recipe details row."""
        return await self.store("recipes").find_one(Criteria().eq("id", recipe_id))

    async def find_recipes_with_count(
        self,
        search: str | None = None,
        recipe_type: str | None = None,
        labels: list[str] | None = None,
        ingredients: list[str] | None = None,
        sort_by: str = "cook_time_minutes",
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """Find recipes and total count in one DB round-trip. Count reflects pre-array-filter rows."""
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

        recipes, total = await self.store("recipes").find(criteria, with_count=True)

        # Filter by labels/ingredients (client-side for simplicity, can be optimized later)
        if labels or ingredients:
            recipes = self._filter_recipes_by_arrays(recipes, labels, ingredients)

        return recipes, total

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

    async def get_recipe_interactions(self, recipe_id: str, user_id: str) -> dict:
        """Get all interactions for a specific recipe and user. Returns dict with liked, cooked, user_rating."""
        interactions = await self.store("recipe_user_interactions").find(
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

    async def get_recipes_interactions_bulk(self, recipe_ids: list[str], user_id: str) -> dict[str, dict]:
        """Get interactions for multiple recipes. Returns dict mapping recipe_id -> {liked, cooked, user_rating}."""
        if not recipe_ids:
            return {}

        interactions = await self.store("recipe_user_interactions").find(
            Criteria().eq("user_id", user_id).in_("recipe_id", recipe_ids)
        )

        result = {recipe_id: {"liked": False, "cooked": False, "user_rating": None} for recipe_id in recipe_ids}
        for interaction in interactions:
            recipe_id = interaction["recipe_id"]
            if interaction["interaction_type"] == "liked":
                result[recipe_id]["liked"] = True
            elif interaction["interaction_type"] == "cooked":
                result[recipe_id]["cooked"] = True
            elif interaction["interaction_type"] == "rated":
                result[recipe_id]["user_rating"] = interaction.get("value")

        return result

    async def has_interaction(self, recipe_id: str, user_id: str, interaction_type: str) -> bool:
        """Check if user has an interaction for recipe."""
        result = await self.store("recipe_user_interactions").find_one(
            Criteria().eq("user_id", user_id).eq("recipe_id", recipe_id).eq("interaction_type", interaction_type)
        )
        return result is not None

    async def add_interaction(
        self, recipe_id: str, user_id: str, interaction_type: str, value: int | None = None
    ) -> dict:
        """Add a user recipe interaction (like, cooked, rated)."""
        return await self.store("recipe_user_interactions").insert(
            {
                "recipe_id": recipe_id,
                "user_id": user_id,
                "interaction_type": interaction_type,
                "value": value,
            }
        )

    async def upsert_interaction(
        self, recipe_id: str, user_id: str, interaction_type: str, value: int | None = None
    ) -> dict:
        """Insert or update a user recipe interaction in a single DB call."""
        return await self.store("recipe_user_interactions").upsert(
            {
                "recipe_id": recipe_id,
                "user_id": user_id,
                "interaction_type": interaction_type,
                "value": value,
            },
            on_conflict="user_id,recipe_id,interaction_type",
        )

    async def remove_interaction(self, recipe_id: str, user_id: str, interaction_type: str) -> bool:
        """Remove a user recipe interaction."""
        criteria = (
            Criteria().eq("user_id", user_id).eq("recipe_id", recipe_id).eq("interaction_type", interaction_type)
        )
        result = await self.store("recipe_user_interactions").delete_where(criteria)
        return len(result) > 0

    # --- grocery items ---

    async def find_grocery_items(self, household_id: str, bought: bool, limit: int | None = None) -> list[dict]:
        criteria = (
            Criteria().eq("household_id", household_id).eq("bought", bought).order("created_at", ascending=False)
        )
        if limit is not None:
            criteria = criteria.limit(limit)
        return await self.store("grocery_items").find(criteria)

    async def find_active_grocery_item(self, household_id: str, norm_name: str) -> dict | None:
        return await self.store("grocery_items").find_one(
            Criteria().eq("household_id", household_id).eq("bought", False).eq("normalized_name", norm_name)
        )

    async def get_grocery_item(self, item_id: str, household_id: str) -> dict | None:
        return await self.store("grocery_items").find_one(
            Criteria().eq("id", item_id).eq("household_id", household_id)
        )

    async def create_grocery_item(
        self,
        household_id: str,
        name: str,
        qty: str | None = None,
        added_by: str | None = None,
        source_recipe_id: str | None = None,
    ) -> dict:
        data: dict = {
            "household_id": household_id,
            "name": name,
            "normalized_name": self._normalize_grocery_name(name),
        }
        if qty is not None:
            data["qty"] = qty
        if added_by is not None:
            data["added_by"] = added_by
        if source_recipe_id is not None:
            data["source_recipe_id"] = source_recipe_id
        return await self.store("grocery_items").insert(data)

    async def update_grocery_item(self, item_id: str, data: dict, household_id: str | None = None) -> dict | None:
        update_data = dict(data)
        if "name" in update_data and isinstance(update_data["name"], str):
            update_data["normalized_name"] = self._normalize_grocery_name(update_data["name"])
        criteria = Criteria().eq("id", item_id)
        if household_id is not None:
            criteria = criteria.eq("household_id", household_id)
        result = await self.store("grocery_items").update_where(criteria, update_data)
        return result[0] if result else None

    async def delete_grocery_item(self, item_id: str, household_id: str | None = None) -> bool:
        criteria = Criteria().eq("id", item_id)
        if household_id is not None:
            criteria = criteria.eq("household_id", household_id)
        result = await self.store("grocery_items").delete_where(criteria)
        return len(result) > 0

    async def get_recipe_titles_by_ids(self, recipe_ids: list[str]) -> dict[str, str]:
        if not recipe_ids:
            return {}
        rows = await self.store("recipes").find(Criteria().in_("id", recipe_ids).select("id,name"))
        return {row["id"]: row["name"] for row in rows}

    async def delete_bought_grocery_items(self, household_id: str) -> None:
        await self.store("grocery_items").delete_where(Criteria().eq("household_id", household_id).eq("bought", True))

    # --- tasks ---

    async def find_tasks_with_count(
        self,
        household_id: str,
        page: int = 1,
        page_size: int = 20,
        include_history: bool = True,
    ) -> tuple[list[dict], int, list[dict], int]:
        """Fetch all household tasks in one DB round-trip, then split/sort/paginate in Python."""
        criteria = Criteria().eq("household_id", household_id)
        if not include_history:
            criteria = criteria.is_("completed_at", None)

        all_tasks = await self.store("tasks").find(criteria)

        active = sorted(
            (t for t in all_tasks if t["completed_at"] is None),
            key=lambda t: (t["due_date"] is None, t["due_date"] or ""),
        )
        history = sorted(
            (t for t in all_tasks if t["completed_at"] is not None),
            key=lambda t: t["completed_at"],
            reverse=True,
        )

        offset = (page - 1) * page_size
        return (
            active[offset : offset + page_size],
            len(active),
            history[offset : offset + page_size],
            len(history),
        )

    async def get_task(self, task_id: str, household_id: str) -> dict | None:
        return await self.store("tasks").find_one(Criteria().eq("id", task_id).eq("household_id", household_id))

    async def create_task(
        self,
        household_id: str,
        name: str,
        assignee_type: str,
        assignee_id: str | None,
        due_date: str | None,
        frequency: str | None,
        created_by: str,
    ) -> dict:
        data: dict = {
            "household_id": household_id,
            "name": name,
            "assignee_type": assignee_type,
            "created_by": created_by,
        }
        if assignee_id is not None:
            data["assignee_id"] = assignee_id
        if due_date is not None:
            data["due_date"] = due_date
        if frequency is not None:
            data["frequency"] = frequency
        return await self.store("tasks").insert(data)

    async def update_task(
        self,
        task_id: str,
        data: dict,
        household_id: str | None = None,
        active_only: bool = False,
    ) -> dict | None:
        criteria = Criteria().eq("id", task_id)
        if household_id is not None:
            criteria = criteria.eq("household_id", household_id)
        if active_only:
            criteria = criteria.is_("completed_at", None)
        result = await self.store("tasks").update_where(criteria, {**data, "updated_at": timestamp()})
        return result[0] if result else None

    async def delete_task(self, task_id: str, household_id: str | None = None, active_only: bool = False) -> bool:
        criteria = Criteria().eq("id", task_id)
        if household_id is not None:
            criteria = criteria.eq("household_id", household_id)
        if active_only:
            criteria = criteria.is_("completed_at", None)
        result = await self.store("tasks").delete_where(criteria)
        return len(result) > 0


def get_repository(request: Request) -> Repository:
    """FastAPI dependency that returns a Repository backed by the shared async client."""
    return Repository(request.app.state.store_client)
