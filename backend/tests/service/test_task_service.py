from unittest.mock import MagicMock

import pytest

from src.db.db import DB
from src.errors import NotFoundException
from src.service.task_service import TaskService

FAKE_USER_ID = "user-111"
FAKE_HOUSEHOLD_ID = "hh-222"
FAKE_HOUSEHOLD = {"id": FAKE_HOUSEHOLD_ID, "name": "Test Home"}
FAKE_TASK_ID = "task-aaa"

FAKE_TASK = {
    "id": FAKE_TASK_ID,
    "household_id": FAKE_HOUSEHOLD_ID,
    "name": "Vacuum living room",
    "assignee_type": "none",
    "assignee_id": None,
    "due_date": None,
    "frequency": None,
    "created_by": FAKE_USER_ID,
    "created_at": "2026-06-18T10:00:00+00:00",
    "updated_at": "2026-06-18T10:00:00+00:00",
    "completed_at": None,
}

FAKE_COMPLETED_TASK = {
    **FAKE_TASK,
    "id": "task-bbb",
    "name": "Take out trash",
    "completed_at": "2026-06-17T08:00:00+00:00",
}


@pytest.fixture
def mock_db():
    db = MagicMock(spec=DB)
    db.get_household_by_user.return_value = FAKE_HOUSEHOLD
    return db


@pytest.fixture
def service(mock_db):
    return TaskService(mock_db)


class TestListTasks:
    def test_returns_active_and_history(self, service, mock_db):
        mock_db.find_tasks_with_count.return_value = ([dict(FAKE_TASK)], 1, [dict(FAKE_COMPLETED_TASK)], 1)

        result = service.list_tasks(FAKE_USER_ID)

        assert len(result["active"]) == 1
        assert len(result["history"]) == 1
        assert result["active_total"] == 1
        assert result["history_total"] == 1

    def test_skips_history_when_not_requested(self, service, mock_db):
        mock_db.find_tasks_with_count.return_value = ([dict(FAKE_TASK)], 1, [], 0)

        result = service.list_tasks(FAKE_USER_ID, include_history=False)

        assert result["history"] == []
        assert result["history_total"] == 0
        mock_db.find_tasks_with_count.assert_called_once_with(
            FAKE_HOUSEHOLD_ID, page=1, page_size=20, include_history=False
        )

    def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.list_tasks(FAKE_USER_ID)

    def test_passes_page_and_page_size_to_db(self, service, mock_db):
        mock_db.find_tasks_with_count.return_value = ([dict(FAKE_TASK)], 5, [], 0)

        result = service.list_tasks(FAKE_USER_ID, page=2, page_size=2)

        mock_db.find_tasks_with_count.assert_called_once_with(
            FAKE_HOUSEHOLD_ID, page=2, page_size=2, include_history=True
        )
        assert result["active_total"] == 5
        assert result["page"] == 2

    def test_uses_single_db_call(self, service, mock_db):
        mock_db.find_tasks_with_count.return_value = ([dict(FAKE_TASK)], 1, [], 0)

        service.list_tasks(FAKE_USER_ID)

        mock_db.find_tasks_with_count.assert_called_once()


class TestCreateTask:
    def test_creates_minimal_task(self, service, mock_db):
        mock_db.create_task.return_value = FAKE_TASK

        result = service.create_task(FAKE_USER_ID, name="Vacuum", assignee_type="none", assignee_id=None, due_date=None, frequency=None)

        assert result == FAKE_TASK
        mock_db.create_task.assert_called_once_with(
            household_id=FAKE_HOUSEHOLD_ID,
            name="Vacuum",
            assignee_type="none",
            assignee_id=None,
            due_date=None,
            frequency=None,
            created_by=FAKE_USER_ID,
        )

    def test_accepts_due_date_as_string(self, service, mock_db):
        mock_db.create_task.return_value = FAKE_TASK

        service.create_task(FAKE_USER_ID, name="Task", assignee_type="none", assignee_id=None, due_date="2026-06-30", frequency=None)

        _, kwargs = mock_db.create_task.call_args
        assert kwargs["due_date"] == "2026-06-30"

    def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.create_task(FAKE_USER_ID, name="Task", assignee_type="none", assignee_id=None, due_date=None, frequency=None)


class TestUpdateTask:
    def test_updates_task_successfully(self, service, mock_db):
        updated = {**FAKE_TASK, "name": "Vacuum bedroom"}
        mock_db.update_task.return_value = updated

        result = service.update_task(FAKE_USER_ID, FAKE_TASK_ID, {"name": "Vacuum bedroom"})

        assert result["name"] == "Vacuum bedroom"
        mock_db.update_task.assert_called_once_with(FAKE_TASK_ID, {"name": "Vacuum bedroom"}, household_id=FAKE_HOUSEHOLD_ID, active_only=True)

    def test_no_prefetch_when_updates_empty(self, service, mock_db):
        mock_db.update_task.return_value = FAKE_TASK

        service.update_task(FAKE_USER_ID, FAKE_TASK_ID, {})

        mock_db.get_task.assert_not_called()
        mock_db.update_task.assert_called_once()

    def test_raises_when_not_found_or_completed(self, service, mock_db):
        mock_db.update_task.return_value = None

        with pytest.raises(NotFoundException):
            service.update_task(FAKE_USER_ID, FAKE_TASK_ID, {"name": "New"})

    def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.update_task(FAKE_USER_ID, FAKE_TASK_ID, {"name": "New"})

    def test_clears_assignee_id_when_type_changes_to_none(self, service, mock_db):
        mock_db.update_task.return_value = {**FAKE_TASK, "assignee_type": "none", "assignee_id": None}

        service.update_task(FAKE_USER_ID, FAKE_TASK_ID, {"assignee_type": "none"})

        args, _ = mock_db.update_task.call_args
        assert args[1]["assignee_id"] is None

    def test_clears_assignee_id_when_type_changes_to_all(self, service, mock_db):
        mock_db.update_task.return_value = {**FAKE_TASK, "assignee_type": "all"}

        service.update_task(FAKE_USER_ID, FAKE_TASK_ID, {"assignee_type": "all"})

        args, _ = mock_db.update_task.call_args
        assert args[1]["assignee_id"] is None

    def test_does_not_mutate_caller_dict(self, service, mock_db):
        mock_db.update_task.return_value = {**FAKE_TASK, "assignee_type": "none"}
        original = {"assignee_type": "none"}

        service.update_task(FAKE_USER_ID, FAKE_TASK_ID, original)

        assert original == {"assignee_type": "none"}

    def test_uses_active_only_guard(self, service, mock_db):
        mock_db.update_task.return_value = FAKE_TASK

        service.update_task(FAKE_USER_ID, FAKE_TASK_ID, {"name": "New"})

        _, kwargs = mock_db.update_task.call_args
        assert kwargs["active_only"] is True


class TestCompleteTask:
    def test_marks_task_as_completed(self, service, mock_db):
        mock_db.update_task.return_value = FAKE_COMPLETED_TASK

        result = service.complete_task(FAKE_USER_ID, FAKE_TASK_ID)

        assert result["completed_at"] is not None
        mock_db.update_task.assert_called_once()
        _, kwargs = mock_db.update_task.call_args
        assert kwargs["active_only"] is True
        assert kwargs["household_id"] == FAKE_HOUSEHOLD_ID

    def test_raises_when_not_found_or_already_completed(self, service, mock_db):
        mock_db.update_task.return_value = None

        with pytest.raises(NotFoundException):
            service.complete_task(FAKE_USER_ID, FAKE_TASK_ID)

    def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.complete_task(FAKE_USER_ID, FAKE_TASK_ID)


class TestDeleteTask:
    def test_deletes_active_task(self, service, mock_db):
        mock_db.delete_task.return_value = True

        service.delete_task(FAKE_USER_ID, FAKE_TASK_ID)

        mock_db.delete_task.assert_called_once_with(FAKE_TASK_ID, household_id=FAKE_HOUSEHOLD_ID, active_only=True)

    def test_raises_when_not_found_or_completed(self, service, mock_db):
        mock_db.delete_task.return_value = False

        with pytest.raises(NotFoundException):
            service.delete_task(FAKE_USER_ID, FAKE_TASK_ID)

    def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.delete_task(FAKE_USER_ID, FAKE_TASK_ID)
