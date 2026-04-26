from supabase import create_client, Client
from src.settings import get_db_settings
from src.utils.logger import logger as log


class DB:
    def __init__(self):
        settings = get_db_settings()
        self.client: Client = create_client(settings.url, settings.service_role_key)

    def get_first_id(self, table_name: str) -> str | None:
        # dummy query to verify db connection and return some data
        result = self.client.table(table_name).select("id").limit(1).execute()
        return result.data[0]["id"] if result.data else None

    def get_entity_by_id(self, table_name: str, entity_id: str):
        result = self.client.table(table_name).select("*").eq("id", entity_id).execute()
        return result.data[0] if result.data else None

    def is_alive(self) -> bool:
        try:
            self.get_first_id("profiles")
            return True
        except Exception as e:
            log.error(f"Database connection failed: {e}")
            return False


def get_db() -> DB:
    """Factory function for DB to allow dependency injection."""
    return DB()
