from supabase import create_client, Client
from src.settings import get_supabase_settings
from src.db.criteria import Criteria
from src.db.store import Store
from src.utils.logger import logger as log


class DB:
    def __init__(self):
        settings = get_supabase_settings()
        self.client: Client = create_client(settings.url, settings.service_role_key)

    def store(self, table_name: str) -> Store:
        """Return a :class:`Store` bound to *table_name*."""
        return Store(self.client, table_name)

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
        result = (
            self.client.table("battery_logs")  # todo: move to store. DB should not handle the client directly
            .update(data)
            .eq("id", log_id)
            .eq("user_id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def delete_battery_log(self, log_id: str, user_id: str) -> bool:
        result = (
            self.client.table("battery_logs")  # todo: move to store. DB should not handle the client directly
            .delete()
            .eq("id", log_id)
            .eq("user_id", user_id)
            .execute()
        )
        return len(result.data) > 0

    def find_battery_logs_by_household(self, household_id: str, start: str, end: str) -> list[dict]:
        return self.store("battery_logs").find(
            Criteria()
            .eq("household_id", household_id)
            .gte("effective_at", start)
            .lte("effective_at", end)
            .order("effective_at", ascending=False)
        )


def get_db() -> DB:
    """Factory function for DB to allow dependency injection."""
    return DB()
