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
        except Exception as e:
            log.error(f"Database connection failed: {e}")
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


def get_db() -> DB:
    """Factory function for DB to allow dependency injection."""
    return DB()
