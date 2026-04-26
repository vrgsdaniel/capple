from typing import Dict

from src.db.db import DB


class UserService:
    """Service for managing user-related operations."""

    def __init__(self, db: DB):
        self.db = db

    def get_first_id(self) -> dict[str, bool]:
        return self.db.get_first_id("profiles") is not None

    def get_user_name_by_id(self, user_id: str) -> Dict | None:
        result = self.db.get_entity_by_id("profiles", user_id)
        if not result:
            return None
        return {"user_name": result["display_name"]}
