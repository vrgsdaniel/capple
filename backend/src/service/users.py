from typing import Dict

from src.errors import ConflictException, NotFoundException
from src.repository.repository import Repository


class UserService:
    """Service for managing user-related operations."""

    def __init__(self, db: Repository):
        self.db = db

    async def get_user_name_by_id(self, user_id: str) -> Dict | None:
        result = await self.db.get_profile_by_id(user_id)
        if not result:
            return None
        return {"user_name": result["display_name"], "avatar_url": result["avatar_url"]}

    async def create_household(self, user_id: str, name: str) -> Dict:
        existing = await self.db.get_household_by_user(user_id)
        if existing:
            raise ConflictException("You already belong to a household. You can only be in one household at a time.")
        household = await self.db.create_household(name, created_by=user_id)
        await self.db.add_member_to_household(household["id"], user_id, role="owner")
        return {"id": household["id"], "name": household["name"], "invite_code": household["invite_code"]}

    async def join_household(self, user_id: str, invite_code: str) -> Dict:
        existing = await self.db.get_household_by_user(user_id)
        if existing:
            raise ConflictException("You already belong to a household. You can only be in one household at a time.")
        household = await self.db.get_household_by_code(invite_code)
        if not household:
            raise NotFoundException("Invalid invite code")
        await self.db.add_member_to_household(household["id"], user_id)
        return {"id": household["id"], "name": household["name"]}

    async def get_household_members(self, user_id: str) -> Dict:
        members = await self.db.get_household_members(user_id)

        me_raw = next((m for m in members if m["id"] == user_id), None)
        if not me_raw:
            raise NotFoundException("You must belong to a household.")

        def to_member(m: dict) -> dict:
            return {"id": m["id"], "name": m["display_name"], "avatar_url": m["avatar_url"]}

        return {
            "me": to_member(me_raw),
            "others": [to_member(m) for m in members if m["id"] != user_id],
        }

    async def get_user_household(self, user_id: str) -> Dict | None:
        result = await self.db.get_household_by_user(user_id)
        if not result:
            return None
        return {
            "id": result["id"],
            "name": result["name"],
            "invite_code": result["invite_code"],
            "role": result["role"],
        }
