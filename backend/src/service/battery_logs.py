from src.db.db import DB
from src.errors import NotFoundException
from src.utils.logger import logger as log


class BatteryLogService:
    def __init__(self, db: DB):
        self.db = db

    def create_battery_log(self, user_id: str, level: int, note: str | None, effective_at: str) -> dict:
        household = self.db.get_household_by_user(user_id)
        if not household:
            raise NotFoundException("You must belong to a household to log battery.")
        return self.db.create_battery_log(
            user_id=user_id,
            household_id=household["id"],
            level=level,
            note=note,
            effective_at=effective_at,
        )

    def update_battery_log(self, user_id: str, log_id: str, updates: dict) -> dict:
        if not updates:
            raise NotFoundException("Battery log not found.")
        result = self.db.update_battery_log(log_id, user_id, updates)
        if not result:
            log.warning(f"Battery log {log_id} not found or not owned by user {user_id}")
            raise NotFoundException("Battery log not found.")
        return result

    def delete_battery_log(self, user_id: str, log_id: str) -> None:
        deleted = self.db.delete_battery_log(log_id, user_id)
        if not deleted:
            log.warning(f"Battery log {log_id} not found or not owned by user {user_id}")
            raise NotFoundException("Battery log not found.")

    def get_household_battery_logs(self, user_id: str, start: str, end: str) -> list[dict]:
        household = self.db.get_household_by_user(user_id)
        if not household:
            raise NotFoundException("You must belong to a household to view battery logs.")
        return self.db.find_battery_logs_by_household(household["id"], start, end)
