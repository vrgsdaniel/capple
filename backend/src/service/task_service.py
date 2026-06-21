from src.repository.repository import Repository
from src.errors import NotFoundException
from src.utils.general import timestamp
from src.utils.logger import logger as log


class TaskService:
    def __init__(self, db: Repository):
        self.db = db

    async def _resolve_household(self, user_id: str) -> str:
        household = await self.db.get_household_by_user(user_id)
        if not household:
            log.warning(f"User {user_id} attempted task operation without a household")
            raise NotFoundException("You must belong to a household to manage tasks.")
        return household["id"]

    async def list_tasks(self, user_id: str, page: int = 1, page_size: int = 20, include_history: bool = True) -> dict:
        household_id = await self._resolve_household(user_id)
        log.info(f"Listing tasks for household {household_id} (page={page}, include_history={include_history})")
        active, active_total, history, history_total = await self.db.find_tasks_with_count(
            household_id, page=page, page_size=page_size, include_history=include_history
        )
        log.info(
            f"Listed {active_total} active and {history_total} history tasks for household {household_id} (page={page})"
        )
        return {
            "active": active,
            "history": history,
            "active_total": active_total,
            "history_total": history_total,
            "page": page,
            "page_size": page_size,
        }

    async def create_task(
        self,
        user_id: str,
        name: str,
        assignee_type: str,
        assignee_id: str | None,
        due_date: str | None,
        frequency: str | None,
    ) -> dict:
        household_id = await self._resolve_household(user_id)
        log.info(f"Creating task '{name}' for household {household_id}")
        return await self.db.create_task(
            household_id=household_id,
            name=name.strip(),
            assignee_type=assignee_type,
            assignee_id=assignee_id,
            due_date=due_date,
            frequency=frequency,
            created_by=user_id,
        )

    async def update_task(self, user_id: str, task_id: str, updates: dict) -> dict:
        household_id = await self._resolve_household(user_id)
        updates = dict(updates)  # copy — don't mutate the caller's dict

        # When changing assignee_type away from 'specific', clear the assignee.
        if "assignee_type" in updates and updates["assignee_type"] != "specific":
            updates["assignee_id"] = None

        log.info(f"Updating task {task_id} in household {household_id} (fields: {list(updates.keys()) or ['none']})")
        result = await self.db.update_task(task_id, updates, household_id=household_id, active_only=True)
        if not result:
            log.warning(f"Task {task_id} not found or already completed in household {household_id}")
            raise NotFoundException("Task not found or already completed.")
        return result

    async def complete_task(self, user_id: str, task_id: str) -> dict:
        household_id = await self._resolve_household(user_id)
        log.info(f"Completing task {task_id} in household {household_id}")
        result = await self.db.update_task(
            task_id,
            {"completed_at": timestamp()},
            household_id=household_id,
            active_only=True,
        )
        if not result:
            log.warning(f"Task {task_id} not found or already completed in household {household_id}")
            raise NotFoundException("Task not found or already completed.")
        return result

    async def delete_task(self, user_id: str, task_id: str) -> None:
        household_id = await self._resolve_household(user_id)
        log.info(f"Deleting task {task_id} from household {household_id}")
        deleted = await self.db.delete_task(task_id, household_id=household_id, active_only=True)
        if not deleted:
            log.warning(f"Task {task_id} not found or already completed in household {household_id}")
            raise NotFoundException("Task not found or already completed.")
