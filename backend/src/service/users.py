from typing import Dict

from src.errors import ConflictException, ForbiddenException, NotFoundException
from src.repository.repository import Repository
from src.utils.logger import logger as log


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
            log.warning("User %s attempted to create a second household", user_id)
            raise ConflictException("You already belong to a household. You can only be in one household at a time.")
        household = await self.db.create_household(name, created_by=user_id)
        try:
            await self.db.add_member_to_household(household["id"], user_id, role="owner")
        except Exception:
            # Roll back the orphaned household — households.created_by has ON DELETE RESTRICT,
            # so an orphan row would permanently block account deletion for this user.
            log.warning("Owner membership insert failed for household %s; rolling back household row", household["id"])
            await self.db.delete_household_by_owner(household["id"], user_id)
            raise
        return {"id": household["id"], "name": household["name"], "invite_code": household["invite_code"]}

    async def join_household(self, user_id: str, invite_code: str) -> Dict:
        existing = await self.db.get_household_by_user(user_id)
        if existing:
            log.warning("User %s attempted to join a second household", user_id)
            raise ConflictException("You already belong to a household. You can only be in one household at a time.")
        household = await self.db.get_household_by_code(invite_code)
        if not household:
            log.warning("User %s provided an invalid invite code", user_id)
            raise NotFoundException("Invalid invite code")
        await self.db.add_member_to_household(household["id"], user_id)
        return {"id": household["id"], "name": household["name"]}

    async def get_household_members(self, user_id: str) -> Dict:
        members = await self.db.get_household_members(user_id)

        me_raw = next((m for m in members if m["id"] == user_id), None)
        if not me_raw:
            log.warning("No household found for user %s", user_id)
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

    async def leave_household(self, user_id: str) -> None:
        household = await self.db.get_household_by_user(user_id)
        if not household:
            log.warning("User %s attempted to leave a household but has no membership", user_id)
            raise NotFoundException("You are not a member of any household.")
        if household["role"] == "owner":
            log.warning("Owner %s attempted to leave household %s instead of deleting it", user_id, household["id"])
            raise ForbiddenException("Owners cannot leave a household. Delete the household instead.")
        removed = await self.db.remove_user_from_household(user_id, household["id"])
        if not removed:
            log.warning("Membership for user %s in household %s was already gone on delete", user_id, household["id"])
            raise NotFoundException("Membership not found.")

    async def delete_household(self, user_id: str) -> None:
        household = await self.db.get_household_by_user(user_id)
        if not household:
            log.warning("User %s attempted to delete a household but has no membership", user_id)
            raise NotFoundException("You are not a member of any household.")
        # Ownership is enforced by the DB query (created_by filter), not just by Python logic.
        deleted = await self.db.delete_household_by_owner(household["id"], user_id)
        if not deleted:
            log.warning("User %s attempted to delete household %s but is not the owner", user_id, household["id"])
            raise ForbiddenException("Only the owner can delete the household.")

    async def delete_account(self, user_id: str) -> None:
        household = await self.db.get_household_by_user(user_id)
        if household and household["role"] == "owner":
            log.warning("User %s attempted to delete account while owning household %s", user_id, household["id"])
            raise ConflictException("You must delete your household before deleting your account.")
        await self.db.delete_user_account(user_id)
