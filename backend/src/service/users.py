from typing import Dict

from src.db.db import DB
from src.errors import NotFoundException


class UserService:
    """Service for managing user-related operations."""

    def __init__(self, db: DB):
        self.db = db

    def get_user_name_by_id(self, user_id: str) -> Dict | None:
        result = self.db.get_profile_by_id(user_id)
        if not result:
            return None
        return {"user_name": result["display_name"], "avatar_url": result["avatar_url"]}

    def create_household(self, user_id: str, name: str) -> Dict:
        household = self.db.create_household(name, created_by=user_id)
        self.db.add_member_to_household(household["id"], user_id, role="owner")
        return {"id": household["id"], "name": household["name"], "invite_code": household["invite_code"]}

    def join_household(self, user_id: str, invite_code: str) -> Dict:
        household = self.db.get_household_by_code(invite_code)
        if not household:
            raise NotFoundException("Invalid invite code")
        self.db.add_member_to_household(household["id"], user_id)
        return {"id": household["id"], "name": household["name"]}

    def get_user_household(self, user_id: str) -> Dict | None:
        result = self.db.get_household_by_user(user_id)
        if not result:
            return None
        return {
            "id": result["id"],
            "name": result["name"],
            "invite_code": result["invite_code"],
            "role": result["role"],
        }
